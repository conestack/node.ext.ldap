###############################################################################
# Makefile for mxenv projects.
###############################################################################

# Defensive settings for make: https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
# for Makefile debugging purposes add -x to the .SHELLFLAGS
.SHELLFLAGS:=-eu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

# Sentinel files
SENTINEL_FOLDER:=.sentinels
SENTINEL:=$(SENTINEL_FOLDER)/about.txt
$(SENTINEL):
	@mkdir -p $(SENTINEL_FOLDER)
	@echo "Sentinels for the Makefile process." > $(SENTINEL)

###############################################################################
# openldap
###############################################################################

OPENLDAP_VERSION?="2.4.59"
OPENLDAP_URL?="https://www.openldap.org/software/download/OpenLDAP/openldap-release/"
OPENLDAP_DIR?=$(shell echo $(realpath .))/openldap
OPENLDAP_ENV?="PATH=/usr/local/bin:/usr/bin:/bin"

OPENLDAP_SENTINEL:=$(SENTINEL_FOLDER)/openldap.sentinel
$(OPENLDAP_SENTINEL): $(SENTINEL)
	@echo "Building openldap server in '$(OPENLDAP_DIR)'"
	@test -d $(OPENLDAP_DIR) || curl -o openldap-$(OPENLDAP_VERSION).tgz \
		$(OPENLDAP_URL)/openldap-$(OPENLDAP_VERSION).tgz
	@test -d $(OPENLDAP_DIR) || tar xf openldap-$(OPENLDAP_VERSION).tgz
	@test -d $(OPENLDAP_DIR) || rm openldap-$(OPENLDAP_VERSION).tgz
	@test -d $(OPENLDAP_DIR) || mv openldap-$(OPENLDAP_VERSION) $(OPENLDAP_DIR)
	@env -i -C $(OPENLDAP_DIR) $(OPENLDAP_ENV) bash -c \
		'./configure \
			--with-tls \
			--enable-slapd=yes \
			--enable-overlays \
			--prefix=$(OPENLDAP_DIR) \
		&& make depend \
		&& make -j4 \
		&& make install'
	@touch $(OPENLDAP_SENTINEL)

.PHONY: openldap
openldap: $(OPENLDAP_SENTINEL)

.PHONY: openldap-dirty
openldap-dirty:
	@test -d $(OPENLDAP_DIR) \
		&& env -i -C $(OPENLDAP_DIR) $(OPENLDAP_ENV) bash -c 'make clean'
	@rm -f $(OPENLDAP_SENTINEL)

.PHONY: openldap-clean
openldap-clean:
	@rm -f $(OPENLDAP_SENTINEL)
	@rm -rf $(OPENLDAP_DIR)

###############################################################################
# venv
###############################################################################

# Flag whether to skip virtual env creation and use host python instead.
# Needed for github actions.
USE_HOST_PYTHON?=

HOST_PYTHON?=python3
HOST_PIP?=pip
VENV_FOLDER?=venv

# Define bin folder and python binary. Leave bin folder empty if using host
# Python, expecting all commands in PATH.
ifeq ($(USE_HOST_PYTHON),)
PYTHON_BIN?=$(VENV_FOLDER)/bin/python
PIP_BIN?=$(VENV_FOLDER)/bin/pip
else
PYTHON_BIN?=$(HOST_PYTHON)
PIP_BIN?=$(HOST_PIP)
endif

VENV_SENTINEL:=$(SENTINEL_FOLDER)/venv.sentinel
$(VENV_SENTINEL): $(SENTINEL)
ifeq ($(USE_HOST_PYTHON),)
	@echo "Setup Python Virtual Environment under '$(VENV_FOLDER)'"
	@$(HOST_PYTHON) -m venv $(VENV_FOLDER)
	@$(PIP_BIN) install -U pip setuptools wheel
else
	@echo "Skip Python Virtual Environment Setup. Use Host Python instead"
endif
	@touch $(VENV_SENTINEL)

.PHONY: venv
venv: $(VENV_SENTINEL)

.PHONY: venv-dirty
venv-dirty:
	@rm -f $(VENV_SENTINEL)

.PHONY: venv-clean
venv-clean: venv-dirty
ifeq ($(USE_HOST_PYTHON),)
	@rm -rf $(VENV_FOLDER)
endif

###############################################################################
# python-ldap
###############################################################################

PYTHON_LDAP_SENTINEL:=$(SENTINEL_FOLDER)/python-ldap.sentinel
$(PYTHON_LDAP_SENTINEL): $(VENV_SENTINEL) $(OPENLDAP_SENTINEL)
	@$(PIP_BIN) install \
		--force-reinstall \
		--no-use-pep517 \
		--global-option=build_ext \
		--global-option="-I$(OPENLDAP_DIR)/include" \
		--global-option="-L$(OPENLDAP_DIR)/lib" \
		--global-option="-R$(OPENLDAP_DIR)/lib" \
		python-ldap
	@touch $(PYTHON_LDAP_SENTINEL)

.PHONY: python-ldap
python-ldap: $(PYTHON_LDAP_SENTINEL)

.PHONY: python-ldap-dirty
python-ldap-dirty:
	@rm -f $(PYTHON_LDAP_SENTINEL)

.PHONY: python-ldap-clean
python-ldap-clean: python-ldap-dirty
	@test -e $(PIP_BIN) && $(PIP_BIN) uninstall -y python-ldap

###############################################################################
# install
###############################################################################

INSTALLED_PACKAGES=.installed.txt

INSTALL_SENTINEL:=$(SENTINEL_FOLDER)/install.sentinel
$(INSTALL_SENTINEL): $(PYTHON_LDAP_SENTINEL)
	@echo "Install python packages"
	@$(PIP_BIN) install -e .[test]
	@$(PIP_BIN) freeze > $(INSTALLED_PACKAGES)
	@touch $(INSTALL_SENTINEL)

.PHONY: install
install: $(INSTALL_SENTINEL)

.PHONY: install-dirty
install-dirty:
	@rm -f $(INSTALL_SENTINEL)

###############################################################################
# system dependencies
###############################################################################

SYSTEM_DEPENDENCIES?=\
	build-essential \
	curl \
	libsasl2-dev \
	libssl-dev \
	libdb-dev \
	libltdl-dev

.PHONY: system-dependencies
system-dependencies:
	@echo "Install system dependencies"
	@test -z "$(SYSTEM_DEPENDENCIES)" && echo "No System dependencies defined"
	@test -z "$(SYSTEM_DEPENDENCIES)" \
		|| sudo apt-get install -y $(SYSTEM_DEPENDENCIES)

###############################################################################
# test
###############################################################################

TEST_COMMAND?=scripts/test.sh

.PHONY: test
test: $(INSTALL_SENTINEL)
	@echo "Run tests"
	@test -z "$(TEST_COMMAND)" && echo "No test command defined"
	@test -z "$(TEST_COMMAND)" || bash -c \
		'export PYTHON_BIN=$(PYTHON_BIN) \
		&& $(TEST_COMMAND)'

###############################################################################
# coverage
###############################################################################

ifeq ($(USE_HOST_PYTHON),)
COVERAGE_BIN?=$(VENV_FOLDER)/bin/coverage
else
COVERAGE_BIN?=coverage
endif

COVERAGE_COMMAND?=scripts/coverage.sh

.PHONY: coverage
coverage: $(INSTALL_SENTINEL)
	@echo "Run coverage"
	@test -z "$(COVERAGE_COMMAND)" && echo "No coverage command defined"
	@test -z "$(COVERAGE_COMMAND)" || bash -c \
		'export PYTHON_BIN=$(PYTHON_BIN) \
		&& export COVERAGE_BIN=$(COVERAGE_BIN) \
		&& $(COVERAGE_COMMAND)'

.PHONY: coverage-clean
coverage-clean:
	@rm -rf .coverage htmlcov

###############################################################################
# clean
###############################################################################

CLEAN_TARGETS?=openldap

.PHONY: clean
clean: venv-clean coverage-clean
	@rm -rf $(CLEAN_TARGETS) .sentinels .installed.txt

.PHONY: runtime-clean
runtime-clean:
	@echo "Remove runtime artifacts, like byte-code and caches."
	@find . -name '*.py[c|o]' -delete
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +
