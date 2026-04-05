from app.schemas import CellSource, EntityRow


def test_entity_row_shape() -> None:
    row = EntityRow(
        entity="Example Co",
        attributes={"website": "https://example.com", "category": "startup"},
        cell_sources={
            "entity": CellSource(
                value="Example Co",
                source_url="https://example.com/about",
                source_title="About Example",
                evidence="Example Co builds AI software.",
            ),
            "website": CellSource(
                value="https://example.com",
                source_url="https://example.com/about",
                source_title="About Example",
                evidence="Visit us at example.com",
            ),
        },
    )
    assert row.cell_sources["entity"].value == "Example Co"
