# CFA VPN app

This app allows you to manage CFA VPN connections allowing you to perform actions such as:

- Generate a new VPN keys based off an email address
- Send the keys to the user

## Installation

Make a copy of the `emails.template.json` file and rename it to `emails.json`. Fill in the details of the email accounts you want to send the keys to. Alternatively, you can use the `CFA_EMAILS_JSON_PATH` environment variable to specify the location of the `emails.json` file.

## Usage

Using pants, package the app using:

```
./pants package cfa_vpn::
```

To see the available commands, run the generated pex file with the `--help` flag:

```
dist/cfa_vpn.py/outline_manager.pex --help
```

To generate a new VPN keys, run the following command:

```
dist/cfa_vpn.py/outline_manager.pex -g
```

To send the keys to the users, run the following command:

```
dist/cfa_vpn.py/outline_manager.pex -s
```

To generate and send the keys to the users, run the following command:

```
dist/cfa_vpn.py/outline_manager.pex -g -s
```
