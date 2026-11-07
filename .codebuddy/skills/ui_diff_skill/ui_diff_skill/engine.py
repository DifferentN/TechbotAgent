from pathlib import Path
from .matching.matcher import match_components
from .matching.lists import detect_repeated_templates
from .diff import geometry,spacing,typography,color,style,fallback_style
from .vision import visual
from .report.writer import write
from .core.models import serializable
from .core.utils import write_json

class UIDiffEngine:
    def __init__(self,config):
        self.config=config

    def run(self,design_adapter,runtime_adapter,outdir,runtime_comparison=None):
        from copy import deepcopy
        from .core.runtime_comparison import prepare_snapshot,complete_runtime_differences
        out=Path(outdir)
        ds=design_adapter.collect(out/"design")
        rs=runtime_adapter.collect(out/"runtime")
        write_json(out/"design"/"design_snapshot.json",serializable(ds))
        write_json(out/"runtime"/"runtime_snapshot.json",serializable(rs))
        config=deepcopy(self.config)
        comparison=None
        if runtime_comparison is not None:
            sources={ds.source,rs.source}
            if "appium-ios" not in sources or not sources.intersection({"android-adb","appium-android"}):
                raise ValueError("Runtime comparison requires Android and iOS snapshots")
            viewport=runtime_comparison.get("viewport",(390,844))
            baseline_rect=runtime_comparison.get("baseline_content_rect",(0,0,1,1))
            target_rect=runtime_comparison.get("target_content_rect",(0,0,1,1))
            semantic_map=runtime_comparison.get("semantic_map",{})
            ds=prepare_snapshot(ds,viewport,baseline_rect,semantic_map)
            rs=prepare_snapshot(rs,viewport,target_rect)
            write_json(out/"design"/"comparison_snapshot.json",serializable(ds))
            write_json(out/"runtime"/"comparison_snapshot.json",serializable(rs))
            config["runtime_comparison"]=True
            comparison={
                "mode":"android-ios-runtime",
                "baseline_source":ds.source,"target_source":rs.source,
                "reference_viewport":list(viewport),"geometry_unit":"reference-logical-unit",
                "baseline_content_rect":list(baseline_rect),"target_content_rect":list(target_rect),
                "semantic_map":semantic_map,
                "limitations":[
                    "Normalized relative layout; reference units are not Android dp or iOS pt.",
                    "UNKNOWN measurements and unmatched components are not passes.",
                    "Native wrapper and accessibility-tree differences can affect matching.",
                    "Screenshots are captured sequentially; align page, data, locale and state first.",
                ],
            }

        matches,missing,unexpected=match_components(ds.components,rs.components)

        diffs=[]
        diffs += geometry.compare(ds,rs,matches,config)
        diffs += spacing.compare_parent_margins(ds,rs,matches,config)
        diffs += spacing.compare_sibling_gaps(ds,rs,matches,config)
        diffs += typography.compare(ds,rs,matches)
        diffs += color.compare(ds,rs,matches,config)
        diffs += style.compare(ds,rs,matches)
        diffs += fallback_style.compare(ds,rs,matches,config)
        diffs += visual.compare(ds,rs,matches,config)
        if comparison is not None:
            diffs += complete_runtime_differences(ds,rs,matches,diffs)

        templates={
            "design_list_templates":detect_repeated_templates(ds.components),
            "runtime_list_templates":detect_repeated_templates(rs.components),
        }
        data=write(out,ds,rs,matches,missing,unexpected,diffs,
                   comparison=comparison,extra=templates)
        write_json(out/"list_templates.json",{
            "design":templates["design_list_templates"],
            "runtime":templates["runtime_list_templates"],
        })
        return data
