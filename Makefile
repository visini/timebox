APP_NAME := "Timebox"

ifdef VERSION
VERSION_SET := 1
endif

install:
	export SYSTEM_VERSION_COMPAT=1
	export LDFLAGS="${LDFLAGS} -L/usr/local/opt/zlib/lib"
	export CPPFLAGS="${CPPFLAGS} -I/usr/local/opt/zlib/include"
	export LDFLAGS="${LDFLAGS} -L/usr/local/opt/sqlite/lib"
	export CPPFLAGS="${CPPFLAGS} -I/usr/local/opt/sqlite/include"
	export PKG_CONFIG_PATH="${PKG_CONFIG_PATH} /usr/local/opt/zlib/lib/pkgconfig"
	export PKG_CONFIG_PATH="${PKG_CONFIG_PATH} /usr/local/opt/sqlite/lib/pkgconfig"
	poetry install
dev:
	poetry run python main.py
compile:
	export APP_NAME=$(APP_NAME) && poetry run python setup.py py2app
debug: compile
	open "dist/$(APP_NAME).app/Contents/MacOS/$(APP_NAME)"
release:
ifeq ($(VERSION_SET),1)
	export VERSION=$(VERSION) && export APP_NAME=$(APP_NAME) && poetry run python setup.py py2app
	poetry version $(VERSION)
	git add pyproject.toml
	git commit -m "Release $(VERSION)"
	git push 
	cd dist && zip -r "$(APP_NAME).app.zip" "$(APP_NAME).app"
	gh release create $(VERSION) 'dist/$(APP_NAME).app.zip#$(APP_NAME).app.zip'
else
	$(error VERSION not defined - use like this: make release VERSION=...)
endif