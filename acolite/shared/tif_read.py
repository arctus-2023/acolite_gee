

def get_tags_meta(tif):
    import rasterio
    with rasterio.open(tif,'r') as f:
        tags, meta = f.tags(),f.meta

    meta.update(tags)
    return meta