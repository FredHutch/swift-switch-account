# Configuration file for sw2account
# Must contain a "default" section
# Each section must contain:
#     v1AuthUrl: URL for V1 authentication
#     v2AuthUrl: URL for V2 authentication
#     auth_version_default: default authentication version
[default]
v1AuthUrl: https://stack.foo.org/auth/v1.0
v2AuthUrl: https://stack.foo.org/auth/v2.0
auth_version_default: v1
#
# add additional sections for other servers/systems
#
# [altstack]
# v1AuthUrl: https://otherstack.foo.org/auth/v1.0
# v2AuthUrl: https://otherstack.foo.org/auth/v2.0
# auth_version_default: v2
