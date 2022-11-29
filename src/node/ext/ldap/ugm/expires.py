from datetime import datetime
import time


EXPIRATION_DAYS = 0
EXPIRATION_SECONDS = 1


class AccountExpiration:
    """Object for handling account expiration.

    Depending on the LDAP schema used, there is different behavior how
    expires attributes is interpreted, e.g. value is in days or seconds
    since epoch, or if additional attribute values should be taken into
    account.

    Therefor it is supposed to subclass this object and overwrite ``get``,
    ``set`` and ``expired`` functions as needed.

    XXX: The base implementation reflects the initial expires attribute
    behavior of ``node.ext.ldap`` and needs to be refactored as it is
    inaccurate.
    """

    def __init__(
        self,
        attribute,
        unit=EXPIRATION_SECONDS,
        whitelist=['-1', '99999']
    ):
        """Create account expiration handler.

        :param attribute: The attribute name containing expiration information.
        :param unit: Expiration value unit. Either ``EXPIRATION_DAYS`` or
            ``EXPIRATION_SECONDS``. Defaults to ``EXPIRATION_SECONDS``.
        :param whitelist: List of values which gets interpretes as "account
            not expires".
        """
        self.attribute = attribute
        self.unit = unit
        self.whitelist = whitelist

    def set(self, attrs, value):
        """Set expiration date of account.

        :param attrs: A mapping containg the user attributes.
        :param value: A ``datetime.datetime`` instance or ``None`` if account
            not expires.
        """
        if not value:
            attrs[self.attribute] = self.whitelist[0]
            return
        if not isinstance(value, datetime):
            raise ValueError('Expires value must be a datetime instance')
        value = time.mktime(value.utctimetuple())
        if self.unit == EXPIRATION_DAYS:
            value /= 86400
        attrs[self.attribute] = str(int(round(value)))

    def get(self, attrs):
        """Get expiration date of account.

        :param attrs: A mapping containg the user attributes.
        :return: Expiration date as ``datetime.datetime`` instance or ``None``
            if account not expires.
        """
        value = self._get_single_value(attrs, self.attribute)
        if not value or value in self.whitelist:
            return None
        value = float(value)
        if self.unit == EXPIRATION_DAYS:
            value *= 86400
        return datetime.utcfromtimestamp(value)

    def expired(self, attrs):
        """Return flag whether account is expired.

        :param attrs: A mapping containg the user attributes.
        """
        value = self._get_single_value(attrs, self.attribute)
        if value and value not in self.whitelist:
            value = int(value)
            now = time.time()
            if self.unit == EXPIRATION_DAYS:
                # numer of days since epoch
                now /= 86400
            return now >= value
        return False

    def _get_single_value(self, attrs, name):
        value = attrs.get(name)
        if isinstance(value, list):  # case direct LDAP query result
            value = value[0]
        return value


# expiration attributes.
account_expiration = dict()

# XXX: whitelist=['0']
account_expiration['shadowExpire'] = AccountExpiration(
    'shadowExpire',
    unit=EXPIRATION_DAYS
)
# account_expiration['AccountExpires'] = AccountExpiration(
#     'AccountExpires',
#     whitelist=['0']
# )

# account_expiration['LoginExpirationTime'] = AccountExpiration(
#     'LoginExpirationTime'
# )

# account_expiration['PwdEndTime'] = AccountExpiration(
#     'PwdEndTime'
# )
