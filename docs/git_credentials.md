# Git Credentials

In order to access private repos `jedi_bundle` uses a `$HOME/.git-credentials` file. This file takes the format:

```
https://username:token@github.com
https://username:token
```

where `username` and `token` are replaced with your own GitHub username and personal access token.

In order to store your token for each clone add the following directive to your `$HOME/.gitconfig`:

``` toml
[credential]
  helper = store
```

For instructions for setting up a personal access token see the [instructions at GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).
