###############################################################################
# python-ldap
###############################################################################

include mk/openldap.mk

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
