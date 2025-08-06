# onsendo

## Adding new data

```bash
poetry run python -m onsen_manager.cli add-onsen \
    --ban_number 1 \
    --name "Takegawara Onsen" \
    --address "Oita Prefecture, Beppu City, Motomachi 16-23"

poetry run python -m onsen_manager.cli add-visit \
    --onsen_id 1 \
    --stay_length_minutes 60 \
    --personal_rating 5 \
    --sauna_visited
```
