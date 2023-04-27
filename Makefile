# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Include my.env and export it so variables set in there are available in the
# Makefile.
include my.env
export

# Set these in the environment to override them. This is helpful for
# development if you have file ownership problems because the user in the
# container doesn't match the user on your host.
APP_UID ?= 10001
APP_GID ?= 10001

DOCKER := $(shell which docker)
DC=${DOCKER} compose

.DEFAULT_GOAL := help
.PHONY: help
help:
	@echo "Usage: make RULE"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' Makefile \
		| grep -v grep \
	    | sed -n 's/^\(.*\): \(.*\)##\(.*\)/\1\3/p' \
	    | column -t  -s '|'
	@echo ""

my.env:
	@if [ ! -f my.env ]; \
	then \
	echo "Copying my.env.dist to my.env..."; \
	cp docker/my.env.dist my.env; \
	fi

.docker-build:
	make build

.PHONY: build
build: my.env  ## | Build docker images.
	${DC} build --build-arg userid=${APP_UID} --build-arg groupid=${APP_GID} app
	touch .docker-build

.PHONY: shell
shell: my.env .docker-build  ## | Open a shell in the app container.
	${DC} run --rm app shell

.PHONY: clean
clean:  ## | Remove all build, test, coverage, and Python artifacts.
	-rm -rf .docker-build* build/ crashdata_mdsw_tmp/
	${DC} rm -f
