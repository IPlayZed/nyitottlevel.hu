"""Build the static vote-data.js file from reviewed roll-call records.

The four plenary JSON files are exports from the HowTheyVote API, which compiles
the European Parliament's official roll-call XML. The 2023 committee vote is
transcribed from the LIBE committee minutes linked in the output.
"""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "2021": Path("/tmp/howtheyvote-134463.json"),
    "2024": Path("/tmp/howtheyvote-167712.json"),
    "2026_march": Path("/tmp/howtheyvote-189270.json"),
    "2026_july": Path("/tmp/howtheyvote-195775.json"),
}

META = {
    "2021": {
        "key": "2021-original",
        "date": "2021. július 6.",
        "short_date": "2021",
        "title": "Az eredeti ideiglenes szabály elfogadása",
        "question": "Elfogadja-e a Parlament a szolgáltatók önkéntes tartalomellenőrzését lehetővé tevő átmeneti kivételt?",
        "result_label": "Elfogadva",
        "meaning": "Az igen az eredeti, ideiglenes ePrivacy-kivétel elfogadását jelentette.",
        "position_labels": {
            "FOR": "A rendelet mellett",
            "AGAINST": "A rendelet ellen",
            "ABSTENTION": "Tartózkodott",
            "DID_NOT_VOTE": "Nem szavazott",
        },
        "official_source": "https://data.europarl.europa.eu/distribution/reds_iPlPv_Rcv/PV-9-2021-07-06-RCV/PV-9-2021-07-06-RCV-FNL_en.xml",
    },
    "2024": {
        "key": "2024-extension",
        "date": "2024. április 10.",
        "short_date": "2024",
        "title": "Az első hosszabbítás",
        "question": "Maradjon-e hatályban az ideiglenes kivétel 2026. április 3-ig?",
        "result_label": "Elfogadva",
        "meaning": "Az igen a 2026-ig tartó hosszabbítást támogatta; a nem ellenezte azt.",
        "position_labels": {
            "FOR": "A hosszabbítás mellett",
            "AGAINST": "A hosszabbítás ellen",
            "ABSTENTION": "Tartózkodott",
            "DID_NOT_VOTE": "Nem szavazott",
        },
        "official_source": "https://data.europarl.europa.eu/distribution/reds_iPlPv_Rcv/PV-9-2024-04-10-RCV/PV-9-2024-04-10-RCV-FNL_en.xml",
    },
    "2026_march": {
        "key": "2026-march-rejection",
        "date": "2026. március 26.",
        "short_date": "2026. márc.",
        "title": "A Bizottság második hosszabbítási javaslata",
        "question": "Elfogadja-e a Parlament a Bizottság újabb hosszabbítási javaslatát?",
        "result_label": "Elutasítva",
        "meaning": "Az igen a Bizottság hosszabbítási javaslatát támogatta; a nem annak elutasítását. A javaslat 228–311 arányban elbukott.",
        "position_labels": {
            "FOR": "A hosszabbítási javaslat mellett",
            "AGAINST": "A hosszabbítási javaslat ellen",
            "ABSTENTION": "Tartózkodott",
            "DID_NOT_VOTE": "Nem szavazott",
        },
        "official_source": "https://data.europarl.europa.eu/distribution/reds_iPlPv_Rcv/PV-10-2026-03-26-RCV/PV-10-2026-03-26-RCV-FNL_en.xml",
    },
    "2026_july": {
        "key": "2026-july-rejection",
        "date": "2026. július 9.",
        "short_date": "2026. júl.",
        "title": "Indítvány a Tanács álláspontjának elutasítására",
        "question": "Elutasítsa-e a Parlament a Tanács által javasolt visszaállítást?",
        "result_label": "Nem érte el a küszöböt",
        "meaning": "Itt az igen az elutasítást — vagyis a Tanács szövegével szembeni fellépést — jelentette. Legalább 360 igen kellett volna; 314 érkezett.",
        "position_labels": {
            "FOR": "A Tanács szövegének elutasítása mellett",
            "AGAINST": "Az elutasítás ellen",
            "ABSTENTION": "Tartózkodott",
            "DID_NOT_VOTE": "Nem szavazott",
        },
        "official_source": "https://data.europarl.europa.eu/distribution/reds_iPlPv_Rcv/PV-10-2026-07-09-RCV/PV-10-2026-07-09-RCV-FNL_en.xml",
    },
}


def compact_plenary(source_key):
    raw = json.loads(INPUTS[source_key].read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("member_votes"), list):
        raise ValueError(f"Invalid vote input for {source_key}: member_votes must be a list")
    if not isinstance(raw.get("stats", {}).get("total"), dict) or not isinstance(raw.get("stats", {}).get("by_group"), list):
        raise ValueError(f"Invalid vote input for {source_key}: missing aggregate statistics")
    if not str(raw.get("id", "")).isdigit():
        raise ValueError(f"Invalid vote input for {source_key}: id must be numeric")
    meta = dict(META[source_key])
    members = []
    for item in raw["member_votes"]:
        member = item["member"]
        members.append(
            {
                "name": member["full_name"],
                "country": member.get("country", {}).get("iso_alpha_2", ""),
                "group": member.get("group", {}).get("short_label", "–"),
                "position": item["position"],
            }
        )
    meta.update(
        {
            "body": "Európai Parlament · plenáris ülés",
            "totals": raw["stats"]["total"],
            "members": sorted(members, key=lambda member: member["name"].casefold()),
            "group_stats": [
                {
                    "group": item["group"]["short_label"],
                    "label": item["group"]["label"],
                    "stats": item["stats"],
                }
                for item in raw["stats"]["by_group"]
            ],
            "explore_source": f"https://howtheyvote.eu/votes/{raw['id']}",
        }
    )
    return meta


COMMITTEE_GROUPS = {
    "FOR": {
        "ECR": ["Margarita de la Pisa Carrión", "Rob Rooken"],
        "ID": ["Annalisa Tardino"],
        "EPP": [
            "Vasile Blaga", "Karolin Braunsberger-Reinhold", "Lena Düpont", "Tomasz Frankowski",
            "Andrzej Halicki", "Rasa Juknevičienė", "Jeroen Lenaers", "Lukas Mandl", "Gabriel Mato",
            "Emil Radev", "Paulo Rangel", "Karlo Ressler", "Laurence Sailliet", "Sara Skyttedal",
            "Tomas Tobé", "Elissavet Vozemberg-Vrionidi", "Javier Zarzalejos", "Juan Ignacio Zoido Álvarez",
        ],
        "Renew": [
            "Abir Al-Sahlani", "Katalin Cseh", "Lucia Ďuriš Nicholsonová", "Sophia in 't Veld",
            "Fabienne Keller", "Ulrike Müller", "Jan-Christoph Oetjen", "Ramona Strugariu", "Yana Toom",
            "Hilde Vautmans",
        ],
        "S&D": [
            "Pietro Bartolo", "Maria Grapini", "Sylvie Guillaume", "Evin Incir", "Marina Kaljurand",
            "Juan Fernando López Aguilar", "Javier Moreno Sánchez", "Matjaž Nemec", "Isabel Santos",
            "Birgit Sippel", "Paul Tang", "Elena Yoncheva",
        ],
        "The Left": ["Konstantinos Arvanitis", "Cornelia Ernst", "Helmut Scholz"],
        "Greens/EFA": ["Patrick Breyer", "Saskia Bricmont", "Damien Carême", "Erik Marquardt", "Diana Riba i Giner"],
    },
    "AGAINST": {"ID": ["Nicolaus Fest"], "NI": ["Milan Uhrík"]},
    "ABSTENTION": {"ECR": ["Beata Kempa"]},
}


def committee_vote():
    members = []
    group_counts = {}
    for position, groups in COMMITTEE_GROUPS.items():
        for group, names in groups.items():
            group_counts.setdefault(group, Counter())[position] += len(names)
            for name in names:
                country = "HU" if name == "Katalin Cseh" else ""
                members.append({"name": name, "country": country, "group": group, "position": position})
    zero = {"FOR": 0, "AGAINST": 0, "ABSTENTION": 0, "DID_NOT_VOTE": None}
    return {
        "key": "2023-libe-position",
        "date": "2023. november 14.",
        "short_date": "2023 · LIBE",
        "title": "A 2.0 parlamenti bizottsági álláspontja",
        "question": "Elfogadja-e a LIBE szakbizottság a módosított jelentést a tartós szabályozási javaslatról?",
        "result_label": "Elfogadva",
        "meaning": "Ez szakbizottsági döntés volt, nem a teljes Parlament végszavazása. A módosított jelentést 51–2 arányban fogadták el, egy tartózkodással.",
        "position_labels": {
            "FOR": "A módosított jelentés mellett",
            "AGAINST": "A módosított jelentés ellen",
            "ABSTENTION": "Tartózkodott",
            "DID_NOT_VOTE": "Nem szavazott",
        },
        "body": "Európai Parlament · LIBE szakbizottság",
        "totals": {"FOR": 51, "AGAINST": 2, "ABSTENTION": 1, "DID_NOT_VOTE": None},
        "members": sorted(members, key=lambda member: member["name"].casefold()),
        "group_stats": [
            {
                "group": group,
                "label": group,
                "stats": {**zero, **counts},
            }
            for group, counts in sorted(group_counts.items())
        ],
        "official_source": "https://www.europarl.europa.eu/doceo/document/LIBE-PV-2023-11-13-1_EN.pdf#page=14",
        "explore_source": "https://oeil.secure.europarl.europa.eu/oeil/en/procedure-file?reference=2022%2F0155%28COD%29",
    }


def main():
    votes = [
        compact_plenary("2021"),
        committee_vote(),
        compact_plenary("2024"),
        compact_plenary("2026_march"),
        compact_plenary("2026_july"),
    ]
    payload = json.dumps(votes, ensure_ascii=False, separators=(",", ":"))
    target = ROOT / "vote-data.js"
    target.write_text(
        "/* Generated by scripts/build_vote_data.py from reviewed roll-call records. */\n"
        f"window.CHAT_CONTROL_VOTES={payload};\n",
        encoding="utf-8",
    )
    print(f"Wrote {target} ({target.stat().st_size:,} bytes, {sum(len(v['members']) for v in votes):,} member positions)")


if __name__ == "__main__":
    main()
