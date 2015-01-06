swift-switch-account
====================

`swift-switch-account` (abbreviated sw2) is a client-server
application that allows individuals to set Swift environment variables
used by `python-swiftclient` for accessing Swift object stores.

## Basic Operations

The sw2 client will prompt the user for their directory password and
the Swift account they wish to access.  Given successful
authentication of the credentials and authorization to the account,
the client will set the environment variables:

- `ST_USER`
- `ST_KEY`

with values appropriate for the Swift account.  If the client is
instructed to persist these environment variables, the client will
write a file called `.swiftrc` (or `.swift.cshrc` for C shell
variants) that can be read in by the shell.

Note that `ST_AUTH` (with the Swift authorization URL) is not set by
either this script nor is it written to a swiftrc file.

If either authorization or authentication fail, the user is notified
with an appropriate error message indicating the cause.  Existing
Swift environment variables and the `.swiftrc` file are left as-is.

## Use

`sw2switch [--server-url=<url>] [--persist] <account>`

Put appropriate Swift credentials into current user's environment for
Swift account `account`.  If `--persist` is specified, Swift
credentials will be written into a file in the user's home directory.

# Install and Setup

## Shell Environment

The environment variable `SW2_AUTH` indicates the root URL where the
script can find the sw2server process. 

Since the script must update the current shell environment, it's
necessary to configure either the user's login or the global
(/etc/profile\*) startup files. Thus, a function needs to be defined
that reads the output of the `sw2switch.py` command into the current
environment via `eval`:

```bash
sw2switch () {
 eval `/path/to/sw2switch.py bash $*; `
}
```


# Internals

## How it Works

The client is run with an argument indicating the Swift account the
user wishes to access.  The client then prompts for the password of the
currently logged-in user account and bundles this information into an
encrypted REST request to the server.  Authentication credentials are
provided to the server as basic HTTP authentication to a URL
containing the Swift account name.

    https://user:password@toolbox.fhcrc.org/swift/account/foo_b

If the credential pass authentication (to the directory) the server
then parses this request.  The authorization group is built by
appending `_grp` to the account name (e.g. `foo_b_grp`).  The server
checks authorization (see [Authorization Logic](#authorization-logic))
for this group and if successful, looks up the Swift account
credentials stored in a text file on the server.  These credentials
(the Swift auth URL, user account, and S3 key) are then encoded as a
JSON response to the client with an HTTP status code of 200.

Minimally the client will set Swift environment variables for the
current session:

- `ST_USER`
- `ST_KEY`

Setting these environment variables is done via a bit of sleight-of-hand
stolen from Modules.  The user must source the init file appropriate for
her shell which installs `sw2switch` as a function.  This function
uses eval to run the script which produces bash-like functions as its
output.

If instructed, the client will write/over-write a file in the current
user's home directory.

## Errors:

### Bad login credentials:

- server returns 401 and empty response
- client indicates login failure on terminal and non-zero exit

### User not a member of appropriate groups

- server returns 403 and empty response
- client indicates that user does not have access to group
  and sets non-zero exit code.

### Swift Group/Account does not exist (i.e. no key)

- server returns 404 and JSON encoded error message
- client relays error message to terminal and non-zero exit

### LDAP connection errors

- server returns 500
- client indicates service unavailable

## Authorization Logic

Authorization for an account is controlled by a user's membership in
an eponymous group or in the eponymous group's `managedBy` entity.

If a user requests access to the Swift account `foo_b`, the server
first checks to see if a group named `foo_b_grp` is in the user's
`memberOf` list.  Next, the user is checked to see if the user is a
member of the group managing the group `foo_b_grp` using the same
`memberOf` check.

If either check succeeds, the credentials for the requested account
are returned.


/* vim: set textwidth=70 : */
