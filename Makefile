examples/collection.json:
	stac msbuildings create-collection $@


examples/pc-collection.json:
	stac msbuildings create-collection $@ \
	 	--description "{{ collection.description }}" \
		--extra-field "msft:storage_account=bingmlbuildings" \
		--extra-field "msft:container=footprints" \
		--extra-field "msft:short_description=Machine learning detected buildings footprints."