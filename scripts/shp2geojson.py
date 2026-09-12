"""
Converte shapefile (SIRGAS2000 UTM 22S, EPSG:31982) para GeoJSON WGS84 (EPSG:4326).
Usa pyshp + pyproj (ambiente com acesso à internet).
Uso: python3 shp2geojson.py <caminho_sem_extensao> <saida.geojson>
Mapeia campos do shapefile para: Parcela, ANO, Ha, PLANTAS, VARIEDADE, UDF
(ajustar o dicionário FIELD_MAP se os nomes de campo variarem entre fazendas).
"""
import sys, json
import shapefile
from pyproj import Transformer

FIELD_MAP = {
    "PARCELA": "Parcela",
    "ANO": "ANO",
    "Area_ha": "Ha",
    "N. PLANTAS": "PLANTAS",
    "VARIEDADES": "VARIEDADE",
    "UDF": "UDF",
}

def convert(shp_base, out_path, src_epsg="EPSG:31982"):
    transformer = Transformer.from_crs(src_epsg, "EPSG:4326", always_xy=True)
    sf = shapefile.Reader(shp_base)

    def reproj_ring(ring):
        return [list(transformer.transform(x, y)) for x, y in ring]

    features = []
    for sr in sf.shapeRecords():
        geom = sr.shape.__geo_interface__
        rec = sr.record.as_dict()

        if geom["type"] == "Polygon":
            new_coords = [reproj_ring(r) for r in geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            new_coords = [[reproj_ring(r) for r in poly] for poly in geom["coordinates"]]
        elif geom["type"] == "LineString":
            new_coords = reproj_ring(geom["coordinates"])
        elif geom["type"] == "MultiLineString":
            new_coords = [reproj_ring(r) for r in geom["coordinates"]]
        else:
            raise Exception("tipo de geometria não tratado: " + geom["type"])

        props = {}
        for src_field, out_field in FIELD_MAP.items():
            if src_field in rec:
                props[out_field] = rec[src_field]

        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": {"type": geom["type"], "coordinates": new_coords}
        })

    fc = {"type": "FeatureCollection", "features": features}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    print(f"OK: {len(features)} features -> {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 shp2geojson.py <shapefile_sem_extensao> <saida.geojson>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
