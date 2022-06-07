examples/collection.json:
	stac msbuildings create-collection $@


examples/pc-collection.json:
	stac msbuildings create-collection $@ \
		--extra-field "msft:storage_account=bingmlbuildings" \
		--extra-field "msft:container=footprints" \
		--extra-field "msft:short_description=Machine learning deteceted buildings footprints."