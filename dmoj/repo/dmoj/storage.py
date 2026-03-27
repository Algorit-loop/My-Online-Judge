from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class LenientManifestStaticFilesStorage(ManifestStaticFilesStorage):
    manifest_strict = False

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except ValueError:
            return name

    def url_converter(self, name, hashed_files, template=None):
        converter = super().url_converter(name, hashed_files, template)

        def lenient_converter(matchobj):
            try:
                return converter(matchobj)
            except ValueError:
                return matchobj.group()

        return lenient_converter