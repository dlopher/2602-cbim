# Desvios face aos IDS de referência

Gerado por `tools/gen_desvios.py` a partir de `tests/golden/known_deviations.yaml`. Não editar à mão.

Total: 43 diferenças documentadas.

Os IDS em `00-ref-ids-gr/` foram feitos manualmente e servem de referência, mas têm erros.
A regra do projeto é que a **folha LOIN corrigida contra o esquema IFC** é a verdade. Abaixo,
cada diferença entre o IDS gerado e o de referência, agrupada por motivo.

Legenda: `+` existe no gerado e falta na referência · `-` existe na referência e falta no gerado.

## bSPT-Geral

Sem diferenças semânticas.

## bSPT-ARQ

**A folha M-Betão foi convertida (com filtro Name ~ .*concrete.*, como no IDS EST); a referência ARQ omitiu-a.**

- `(gerado) M-Betão | especificação só no gerado (IFCMATERIAL)`

**A folha marca o requisito na fase 'Projeto de Execução'; a referência omitiu-o.**

- `AQR-Paredes | requisito + property Qto_WallBaseQuantities.Length (IFCLENGTHMEASURE)`
- `ARQ-Coberturas | requisito + property Pset_RoofCommon.IsExternal (IFCBOOLEAN)`

**Gralha na referência (ex.: 'Lenght', 'ValveMechanisme'); o gerado usa o nome do esquema IFC.**

- `ARQ-Guardas | requisito + property Qto_RailingBaseQuantities.Length (IFCLENGTHMEASURE)`
- `ARQ-Guardas | requisito - property Qto_RailingBaseQuantities.Lenght (IFCPOSITIVELENGTHMEASURE)`

**A folha não marca OperationType; a referência acrescentou-o.**

- `ARQ-Portas | requisito - attribute OperationType`

**O gerado exige sempre o atributo PredefinedType quando a folha o marca; a referência bSPT omitiu-o em Rodapés.**

- `ARQ-Rodapes | requisito + attribute PredefinedType`

## bSPT-EST

**A referência repete o mesmo requisito; o gerado não duplica.**

- `EST-Escadas | referência duplicada property Pset_StairCommon.NumberOfRiser (IFCCOUNTMEASURE)`
- `EST-Pilares | referência duplicada property Qto_ColumnBaseQuantities.NetVolume (IFCVOLUMEMEASURE)`

**A folha marca o requisito na fase 'Projeto de Execução'; a referência omitiu-o.**

- `EST-Sapatas | requisito + property Qto_FootingBaseQuantities.Height (IFCLENGTHMEASURE)`
- `EST-Sapatas | requisito + property Qto_FootingBaseQuantities.OuterSurfaceArea (IFCAREAMEASURE)`

## bSPT-MEP

**A folha marca o requisito na fase 'Projeto de Execução'; a referência omitiu-o.**

- `MEP-CaixasVisita | requisito + material`
- `MEP-Difusores | requisito + material`
- `MEP-QuadrosElectricos | requisito + material`

**Gralha na referência (ex.: 'Lenght', 'ValveMechanisme'); o gerado usa o nome do esquema IFC.**

- `MEP-Condutas | requisito + property Qto_DuctSegmentBaseQuantities.Length (IFCLENGTHMEASURE)`
- `MEP-Condutas | requisito - property Qto_DuctSegmentBaseQuantities.Lenght (IFCLENGTHMEASURE)`
- `MEP-Esteiras | requisito + property Qto_CableCarrierSegmentBaseQuantities.Length (IFCLENGTHMEASURE)`
- `MEP-Esteiras | requisito - property Qto_CableCarrierSegmentBaseQuantities.Lenght (IFCLENGTHMEASURE)`

## SRU0198-Geral

Sem diferenças semânticas.

## SRU0198-ARQ

**Em IFC4X3 o enumerado IfcCoveringTypeEnum inclui COPING e TOPPING; a referência usou a lista do IFC4.**

- `ARQ-RevPavCobTet | aplicabilidade + attribute PredefinedType∈{CEILING,CLADDING,COPING,FLOORING,INSULATION,MEMBRANE,MOLDING,NOTDEFINED,ROOFING,SLEEVING,TOPPING,USERDEFINED,WRAPPING}`
- `ARQ-RevPavCobTet | aplicabilidade - attribute PredefinedType∈{CEILING,CLADDING,FLOORING,INSULATION,MEMBRANE,MOLDING,NOTDEFINED,ROOFING,SLEEVING,USERDEFINED,WRAPPING}`

## SRU0198-EST

**A referência troca as entidades: 'Lanço de escadas' tem de ser IfcStairFlight e 'Lanço de rampas' IfcRampFlight (e os Qto respetivos).**

- `EST-LancoEscadas | aplicabilidade + entity IFCSTAIRFLIGHT`
- `EST-LancoEscadas | aplicabilidade - entity IFCRAMPFLIGHT`
- `EST-LancoEscadas | requisito + property Qto_StairFlightBaseQuantities.NetVolume (IFCVOLUMEMEASURE)`
- `EST-LancoEscadas | requisito - property Qto_RampFlightBaseQuantities.NetVolume (IFCVOLUMEMEASURE)`
- `EST-LancoRampas | aplicabilidade + entity IFCRAMPFLIGHT`
- `EST-LancoRampas | aplicabilidade - entity IFCSTAIRFLIGHT`
- `EST-LancoRampas | requisito + property Qto_RampFlightBaseQuantities.NetVolume (IFCVOLUMEMEASURE)`
- `EST-LancoRampas | requisito - property Qto_StairFlightBaseQuantities.NetVolume (IFCVOLUMEMEASURE)`

## SRU0198-MEP

**dataType da referência diferente do esquema IFC oficial (ifcopenshell); o gerado segue o esquema.**

- `MEP-CaixasDerivacao | requisito + property Pset_JunctionBoxTypeCommon.NumberOfGangs (IFCCOUNTMEASURE)`
- `MEP-CaixasDerivacao | requisito - property Pset_JunctionBoxTypeCommon.NumberOfGangs (IFCINTEGER)`
- `MEP-Comutadores | requisito + property Pset_SwitchingDeviceTypeCommon.NumberOfGangs (IFCCOUNTMEASURE)`
- `MEP-Comutadores | requisito - property Pset_SwitchingDeviceTypeCommon.NumberOfGangs (IFCINTEGER)`
- `MEP-Tomadas | requisito + property Pset_OutletTypeCommon.NumberOfSockets (IFCCOUNTMEASURE)`
- `MEP-Tomadas | requisito - property Pset_OutletTypeCommon.NumberOfSockets (IFCINTEGER)`

**A referência repete o mesmo requisito; o gerado não duplica.**

- `MEP-Condutas | referência duplicada property Qto_DuctSegmentBaseQuantities.OuterSurfaceArea (IFCAREAMEASURE)`

**A folha marca o requisito na fase 'Projeto de Execução'; a referência omitiu-o.**

- `MEP-Condutas | requisito + property Qto_DuctSegmentBaseQuantities.GrossCrossSectionArea (IFCAREAMEASURE)`
- `MEP-QuadrosElectricos | requisito + attribute Tag`

**Gralha na referência (ex.: 'Lenght', 'ValveMechanisme'); o gerado usa o nome do esquema IFC.**

- `MEP-Condutas | requisito + property Qto_DuctSegmentBaseQuantities.Length (IFCLENGTHMEASURE)`
- `MEP-Condutas | requisito - property Qto_DuctSegmentBaseQuantities.Lenght (IFCLENGTHMEASURE)`
- `MEP-Esteiras | requisito + property Qto_CableCarrierSegmentBaseQuantities.Length (IFCLENGTHMEASURE)`
- `MEP-Esteiras | requisito - property Qto_CableCarrierSegmentBaseQuantities.Lenght (IFCLENGTHMEASURE)`
- `MEP-Valvulas | requisito + property Pset_ValveTypeCommon.ValveMechanism (IFCLABEL)`
- `MEP-Valvulas | requisito - property Pset_ValveTypeCommon.ValveMechanisme (IFCVALVETYPEENUM)`
