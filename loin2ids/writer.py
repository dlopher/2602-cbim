"""Blocos normalizados → documento IDS 1.0 (via ifctester, que garante a estrutura do XSD)."""
from __future__ import annotations

from ifctester import ids

from .decisions import Project
from .model import Block


def _value(values=None, pattern=None, single=None):
    if single is not None:
        return single
    if pattern is not None:
        return ids.Restriction(options={"pattern": pattern})
    if values:
        if len(values) == 1:
            return values[0]
        return ids.Restriction(options={"enumeration": list(values)})
    return None


def build_ids(blocks: list[Block], project: Project) -> ids.Ids:
    doc = ids.Ids(title=project.title, copyright=project.copyright, version=project.version,
                  description=project.description, author=project.author, date=project.date,
                  purpose=project.purpose, milestone=project.milestone)
    for b in blocks:
        spec = ids.Specification(name=b.name, ifcVersion=[project.ifc_version], identifier=b.identifier,
                                 minOccurs=project.min_occurs, maxOccurs="unbounded")
        spec.applicability.append(ids.Entity(name=b.entity.upper()))
        for f in b.filters:
            spec.applicability.append(ids.Attribute(name=f.attribute, value=_value(f.values, f.pattern)))
        for c in b.classes:
            spec.requirements.append(ids.Classification(system=c.system, value=_value(pattern=c.pattern),
                                                        cardinality="required"))
        for a in b.attrs:
            spec.requirements.append(ids.Attribute(name=a.name, value=a.value, cardinality="required"))
        for p in b.props:
            spec.requirements.append(ids.Property(propertySet=p.pset, baseName=p.name, value=p.value,
                                                  dataType=p.data_type, cardinality="required"))
        for m in b.materials:
            spec.requirements.append(ids.Material(value=m.value, cardinality="required"))
        doc.specifications.append(spec)
    return doc


def to_xml(doc: ids.Ids) -> str:
    xml = doc.to_string()
    if not xml.startswith("<?xml"):
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml
    return xml if xml.endswith("\n") else xml + "\n"
