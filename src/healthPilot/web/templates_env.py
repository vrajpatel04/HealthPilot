from pathlib import Path

from fastapi.templating import Jinja2Templates

from healthPilot.models.enums import ProductCategory

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.cache = None

CATEGORY_LABELS = {
    ProductCategory.sleep: "Sleep",
    ProductCategory.fitness: "Fitness",
    ProductCategory.nutrition: "Nutrition",
    ProductCategory.mental_wellness: "Mental Wellness",
    ProductCategory.lifestyle: "Lifestyle",
}


def category_choices() -> list[tuple[str, str]]:
    return [(c.value, CATEGORY_LABELS[c]) for c in ProductCategory]
