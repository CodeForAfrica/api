## TwoopsTracker

A Twitter-based disinformation tracking tool built on a web-based dashboard that collects deleted tweet content from previously identified trolls and disinformation actors. The project seeks to help monitor the social posts of known disinfo actors. The primary tangible output of the project is to expose trolls behind toxic disinformation campaigns who routinely cover their tracks by deleting original inflammatory social media posts that sparked hate speech, disinformation campaigns or conspiracy theories.

## Getting Started

First create `.env` file in the app directory. From project root directory,

```sh
cp  twoops_tracker/.env.template twoops_tracker/.env
```

and modify the `.env` file according to your needs.

## Build

To build a pex binary, run:

```sh
./pants package twoops_tracker/py:twoopstracker
```

To build the docker image, run:

```sh
VERSION=$(cat twoops_tracker/py/VERSION) ./pants package twoops_tracker/docker:twoopstracker
```

## Run

To run pex binary, execute:

```sh
./pants run twoops_tracker/py:twoopstracker
```

To run the built docker image, execute:

```sh
docker-compose --env-file ./twoops_tracker/.env up twoopstracker
```

**NOTE**: You may need to run `postres` container first to make sure database
is ready to receive connections _before_ starting the `twoopstracker` app.

To do so, run:

```sh
docker-compose --env-file ./twoops_tracker/.env up db
```
