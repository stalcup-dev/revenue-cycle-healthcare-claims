$env:OFFLINE="1"
$env:INCLUDE_GENERATED_ON="1"
$env:JUPYTER_ALLOW_INSECURE_WRITES="1"

python -m nbconvert --execute --to notebook --inplace notebooks\nb01_metric_lineage_audit.ipynb
python -m nbconvert --execute --to notebook --inplace notebooks\nb03_exec_overview_artifact.ipynb
python -m nbconvert --execute --to notebook --inplace notebooks\nb04_driver_pareto_story.ipynb
python -m nbconvert --execute --to notebook --inplace notebooks\nb05_workqueue_story.ipynb

python -m scripts.publish_story_pack
