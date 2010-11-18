##############################################################################
#
# Copyright (c) 2006-2009 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

try:
    from hashlib import sha1
except ImportError: # Python < 2.5
    from sha import new as sha1
import datetime
import logging
import os
import os.path
import setuptools.archive_util
import shutil
import tempfile
import zc.buildout
import zc.buildout.download


def system(c):
    if os.system(c):
        raise SystemError("Failed", c)


class Recipe(object):

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        directory = buildout['buildout']['directory']
        download_cache = buildout['buildout'].get('download-cache')

        location = options.get(
            'location', buildout['buildout']['parts-directory'])
        options['location'] = os.path.join(location, name)

        self.url = self.options['url']
        extra_options = self.options.get('extra_options', '')
        # get rid of any newlines that may be in the options so they
        # do not get passed through to the commandline
        self.extra_options = ' '.join(extra_options.split())

        self.autogen = self.options.get('autogen', '')

        self.patch = self.options.get('patch', '')
        self.patch_options = self.options.get('patch_options', '-p0')

        self.environ = self.options.get('environment', '').split()
        if self.environ:
            self.environ = dict([x.split('=', 1) for x in self.environ])
        else:
            self.environ = {}

        self.source_directory_contains = self.options.get(
            'source-directory-contains', 'configure')
        self.configure_cmd = self.options.get(
            'configure-command', './configure')
        self.configure_options = self.options.get('configure-options', None)
        if self.configure_options:
            self.configure_options = ' '.join(self.configure_options.split())

        self.shared = options.get('shared', None)
        if self.shared:
            if os.path.isdir(self.shared):
                # to prevent nasty surprises, don't use the directory directly
                # since we remove it in case of build errors
                self.shared = os.path.join(self.shared, 'cmmi')
            else:
                if not download_cache:
                    raise ValueError(
                        "Set the 'shared' option of zc.recipe.cmmi to an existing"
                        " directory, or set ${buildout:download-cache}")

                self.shared = os.path.join(
                    directory, download_cache, 'cmmi', 'build')
                self.shared = os.path.join(self.shared, self._state_hash())

            options['location'] = self.shared

    def _state_hash(self):
        # hash of our configuration state, so that e.g. different
        # ./configure options will get a different build directory
        env = ''.join(['%s%s' % (key, value) for key, value
                       in self.environ.items()])
        state = [self.url, self.extra_options, self.autogen,
                 self.patch, self.patch_options, env]
        return sha1(''.join(state)).hexdigest()

    def install(self):
        logger = logging.getLogger(self.name)
        download = zc.buildout.download.Download(
            self.buildout['buildout'], namespace='cmmi', hash_name=True,
            logger=logger)

        if self.shared:
            if os.path.isdir(self.shared):
                logger.info('using existing shared build')
                return self.shared

        fname, is_temp = download(self.url, md5sum=self.options.get('md5sum'))

        # now unpack and work as normal
        tmp = tempfile.mkdtemp('buildout-'+self.name)
        logger.info('Unpacking and configuring')
        try:
            setuptools.archive_util.unpack_archive(fname, tmp)
        finally:
            if is_temp:
                os.remove(fname)

        for key, value in self.environ.items():
            logger.info('Updating environment: %s=%s' % (key, value))
        os.environ.update(self.environ)

        # XXX This is probably more complicated than it needs to be. I
        # retained the distinction between makedirs and mkdir when I moved
        # creation of the build dir after downloading the source since I
        # didn't understand the reason for the distinction. (tlotze)
        if self.shared and not os.path.isdir(self.shared):
            os.makedirs(self.shared)
        dest = self.options['location']
        if not os.path.exists(dest):
            os.mkdir(dest)

        try:
            here = os.getcwd()
            os.chdir(tmp)
            try:
                if not (os.path.exists(self.source_directory_contains) or
                        (self.autogen and os.path.exists(self.autogen))):
                    entries = os.listdir(tmp)
                    if len(entries) == 1:
                        os.chdir(entries[0])
                if self.patch is not '':
                    # patch may be a filesystem path or url
                    # url patches can go through the cache
                    if self.patch is not '':
                        try:
                            self.patch, is_temp = download(
                                self.patch,
                                md5sum=self.options.get('patch-md5sum'))
                        except:
                            # If download/checksum of the patch fails, leaving
                            # the tmp dir won't be helpful.
                            shutil.rmtree(tmp)
                            raise
                    try:
                        system("patch %s < %s"
                               % (self.patch_options, self.patch))
                    finally:
                        if is_temp:
                            os.remove(self.patch)
                if self.autogen is not '':
                    logger.info('auto generating configure files')
                    system("./%s" % self.autogen)
                if not os.path.exists(self.source_directory_contains):
                    entries = os.listdir(tmp)
                    if len(entries) == 1:
                        os.chdir(entries[0])
                    else:
                        raise ValueError("Couldn't find configure")
                self.cmmi(dest)
                shutil.rmtree(tmp)
            finally:
                os.chdir(here)
        except:
            shutil.rmtree(dest)
            if os.path.exists(tmp):
                logger.error("cmmi failed: %s", tmp)
            raise

        return dest

    def update(self):
        pass

    def cmmi(self, dest):
        """Do the 'configure; make; make install' command sequence.

        When this is called, the current working directory is the
        source directory.  The 'dest' parameter specifies the
        installation prefix.

        This can be overridden by subclasses to support packages whose
        command sequence is different.
        """
        options = self.configure_options
        if options is None:
            options = '--prefix=%s' % dest
        if self.extra_options:
            options += ' %s' % self.extra_options
        system("%s %s" % (self.configure_cmd, options))
        system("make")
        system("make install")
