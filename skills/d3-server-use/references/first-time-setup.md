# First-time setup

Walk the user through the steps that are still missing (SKILL.md, step 0 decides which). The user runs the key
commands and edits their own files; Claude explains, checks the result and stores the answers in `<site>`. Server
addresses come from the admin's mails and go into `<site>`, never into a repository.

## 1. Account

The admin creates an account (ssh and JupyterHub) only for users who sent their **public** ssh key. Without an
account, `ssh` answers `Permission denied (publickey)` even with a correct key. Login names follow the admin's
scheme (e.g. the first two letters of first and last name).

## 2. Key pair (skip if the user has one they want to use)

Check first: `ls ~/.ssh/*.pub`. An existing `id_ed25519.pub` is fine.

```bash
ssh-keygen -t ed25519 -C "<login>@kiregio"     # choose a passphrase; files: ~/.ssh/id_ed25519 and .pub
```

- macOS: `ssh-add --apple-use-keychain ~/.ssh/id_ed25519` keeps the passphrase in the keychain.
- Windows: the same command in PowerShell (OpenSSH is built in); files in `C:\Users\<you>\.ssh\`.

Send only `~/.ssh/id_ed25519.pub` (one line starting with `ssh-ed25519`) to the admin. The private key never leaves
the computer; Claude never reads, copies or prints it. On the server the admin manages the keys
(`/etc/ssh/authorized_keys/<login>`), so `~/.ssh/authorized_keys` there has no effect.

## 3. Host block (skip if one already points to the server)

Add to `~/.ssh/config` (create it with mode 600 if it does not exist):

```
Host kiregio
    HostName <server address from the admin's mail>
    User <login>
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
    # reuse one connection for many short commands (watchers, d3run calls); not on Windows
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
    # macOS keychain; IgnoreUnknown keeps Linux from failing on it
    IgnoreUnknown UseKeychain
    UseKeychain yes
    AddKeysToAgent yes
```

Any alias works; store the one the user picks as `ssh_alias` in `<site>`. An existing alias (e.g. one named after the
address) is just as good: do not create a second one.

## 4. First login and test

```bash
ssh kiregio hostname
```

- The first connection asks to confirm the host key. The admin's mail says whether the fingerprint changed; if ssh
  reports a **changed** host key, stop and ask the admin before removing the old entry from `~/.ssh/known_hosts`.
- `Permission denied (publickey)`: the account does not exist yet or the admin has a different key; check
  `ssh -v kiregio` for the key offered.
- It works: test the non-interactive form Claude uses, `ssh -o BatchMode=yes -o ConnectTimeout=10 kiregio hostname`,
  and store the date in `ssh_ok`.

## 5. JupyterHub and certificate

- JupyterHub runs on https only (port 8000; URL from the admin's mail, stored as `jupyterhub_url`). The account is
  created with the server account and starts with a default password from the admin's mail: change it at once under
  `/hub/change-password`. A notebook gets at most one GPU; more GPUs only through `sbatch`.
- Browsers warn about the certificate until the KiRegio root CA is imported, once per computer. Download `ca.crt`
  from the address in the admin's mail (accept the warning for this one file), then:
  - macOS: double-click, add to the "login" keychain; in Keychain Access open "KiRegio Root CA", Trust, "When using
    this certificate: Always Trust".
  - Windows: double-click, compare the SHA-1 thumbprint under Details with the admin's mail, then Install
    Certificate, Current User, "Trusted Root Certification Authorities".
- Grafana (utilization, storage, home quota) has a shared login from the admin's mail. It stays in the mail or a
  password manager.

## 6. A Jupyter kernel for a project (optional)

```bash
cd <proj> && uv add --dev ipykernel
uv run python -m ipykernel install --user --name=<project> --display-name="Python (<project>)"
# remove: jupyter kernelspec uninstall <project>
```

## 7. What `<site>` holds afterwards

`login`, `ssh_alias`, `host`, `ssh_ok`, the JupyterHub and Grafana URLs, and the S3 answer (SKILL.md step 0.3).
Never a password, key or token.
