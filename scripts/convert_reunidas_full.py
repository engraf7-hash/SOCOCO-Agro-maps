import shapefile, json, os
from pyproj import Transformer

SRC = "/home/claude/work/src_reunidas3/REUNIDAS SOCOCO"
OUT = "/home/claude/work/data/reunidas"
os.makedirs(OUT, exist_ok=True)

transformer = Transformer.from_crs("EPSG:31982", "EPSG:4326", always_xy=True)

def reproj_ring(ring):
    return [list(transformer.transform(x, y)) for x, y in ring]

def reproj_coords(gtype, coords):
    if gtype == "Polygon":
        return [reproj_ring(r) for r in coords]
    elif gtype == "MultiPolygon":
        return [[reproj_ring(r) for r in poly] for poly in coords]
    elif gtype == "LineString":
        return reproj_ring(coords)
    elif gtype == "MultiLineString":
        return [reproj_ring(r) for r in coords]
    elif gtype == "Point":
        return list(transformer.transform(coords[0], coords[1]))
    else:
        raise Exception("tipo não tratado: " + gtype)

FIELD_MAP = {
    "PARCELA": "Parcela", "ANO": "ANO", "Area_ha": "Ha",
    "N. PLANTAS": "PLANTAS", "VARIEDADES": "VARIEDADE", "UDF": "UDF",
}

# (subpasta/base, nome de saída, nome de exibição)
LAYERS = [
    ("PARCELAS - REUNIDAS SOCOCO/PARCELAS_REUNIDAS_SOCOCO", "parcelas_geral", "Parcelas — Geral"),
    ("3 TUBOS/3TUBOS", "3_tubos", "3 Tubos"),
    ("AREA BAIXINHA/AREA_BAIXINHA", "area_baixinha", "Área Baixinha"),
    ("AREA EVARISTO/AREA-EVARISTO", "area_evaristo", "Área Evaristo"),
    ("AREA FROTA/AREA_FROTA", "area_frota", "Área Frota"),
    ("AREA MALAM/MALAM", "area_malam", "Área Malam"),
    ("AREA P03/AREA_P03", "area_p03", "Área P03"),
    ("AREA VIVEIRO/VIVEIRO", "area_viveiro", "Área Viveiro"),
    ("BASE INDUSTRIAL/BASE_INDUSTRIAL", "base_industrial", "Base Industrial"),
    ("BLOCO  GRINGO/BLOCO_GRINGO", "bloco_gringo", "Bloco Gringo"),
    ("BLOCO 10/BLOCO-10", "bloco_10", "Bloco 10"),
    ("BLOCO AREIAL/BLOCO_AREAL", "bloco_areal", "Bloco Areial"),
    ("BURRARIA VELHA/BURRARIA_VELHA", "burraria_velha", "Burraria Velha"),
    ("BURREIRO15/BURREIRO15", "burreiro15", "Burreiro 15"),
    ("CC-03/CC-03", "cc_03", "CC-03"),
    ("EXPERIMENTO YARA/EXPERIMENTO_YARA", "experimento_yara", "Experimento Yara"),
    ("PORT#U00c3O DO JAPONES/PORTAO_JAPONES/PORTAO-_JAPONES", "portao_japones", "Portão do Japonês"),
    ("ESTRADAS - SOCOCO REUNIDAS/ESTRADAS", "estradas", "Estradas"),
    ("AREA ADMINISTRATIVO/ADMINISTRATIVO", "area_administrativo", "Área Administrativo"),
    ("AREA-IMOVEL", "area_imovel", "Área do Imóvel"),
]

results = []
for rel, outname, display in LAYERS:
    base = os.path.join(SRC, rel)
    sf = shapefile.Reader(base)
    fields = [f[0] for f in sf.fields[1:]]
    features = []
    for sr in sf.shapeRecords():
        geom = sr.shape.__geo_interface__
        rec = sr.record.as_dict()
        new_coords = reproj_coords(geom["type"], geom["coordinates"])

        if "PARCELA" in fields:
            props = {}
            for src_f, out_f in FIELD_MAP.items():
                if src_f in rec:
                    props[out_f] = rec[src_f]
            # rename H-125 -> H-135
            if props.get("Parcela") == "H-125":
                props["Parcela"] = "H-135"
        else:
            props = rec

        features.append({
            "type": "Feature",
            "properties": props,
            "geometry": {"type": geom["type"], "coordinates": new_coords}
        })

    fc = {"type": "FeatureCollection", "features": features}
    outpath = os.path.join(OUT, outname + ".geojson")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)
    results.append((outname, display, len(features)))
    print(f"OK {outname:25s} {len(features):4d} features")

print()
for r in results:
    print(r)
