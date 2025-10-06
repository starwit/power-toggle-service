.PHONY: install build-deb clean

export PACKAGE_NAME=power-toggle-switch
RELEASEMSG = ${RELEASE_MSG}

EMAIL      := foss@starwit.de
NAME       := Build Bot

install:
	poetry install

settings.yaml:
	cp settings.template.yaml settings.yaml

test: install
	poetry run pytest

set-version:
	$(eval VERSION := $(shell poetry version -s))
	@echo $(VERSION)
	dch --newversion "$(VERSION)" \
	    --maintmaint \
	    --controlmaint \
	    --distribution unstable \
	    --changelog debian/changelog \
	    --vendor "" \
	    --force-distribution \
	    "$(RELEASEMSG)" \
	    -- \
	    --author "$(NAME) <$(EMAIL)>"

build-deb: settings.yaml set-version

	poetry export --without-hashes --format=requirements.txt > requirements.txt

	@echo "Build package"
	dpkg-buildpackage --no-sign

	mkdir -p target
	mv ../${PACKAGE_NAME}_* target/

clean:
	rm -rf dist
	rm -rf target
	rm -rf *.egg-info
	rm -rf debian/.debhelper
	rm -f debian/files
	rm -f debian/*.substvars
	rm -f debian/*.log
	rm -f debian/debhelper-build-stamp
	rm -f debian/${PACKAGE_NAME}.postinst.debhelper
	rm -f debian/${PACKAGE_NAME}.postrm.debhelper
	rm -f debian/${PACKAGE_NAME}.prerm.debhelper
	rm -rf debian/${PACKAGE_NAME}
	rm -f *.tar.gz
	rm -f requirements.txt