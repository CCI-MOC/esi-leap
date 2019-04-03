import oslo_i18n as i18n

_translators = i18n.TranslatorFactory(domain='esi-leap')

# The primary translation function using the well-known name "_"
_ = _translators.primary
