"""Unit tests for HuggingFaceHubSearch component methods and helper functions."""

from __future__ import annotations

import json

import pytest

from huggingface_hub_search import (
    _RESULT_LIMIT_DEFAULT,
    _RESULT_LIMIT_MAX,
    HuggingFaceHubSearch,
    _build_filters_html,
    _normalize_search_type,
)

# ---------------------------------------------------------------------------
# _normalize_search_type
# ---------------------------------------------------------------------------


class TestNormalizeSearchType:
    def test_all_returns_all(self) -> None:
        assert _normalize_search_type("all") == "all"

    def test_single_valid_string_model(self) -> None:
        assert _normalize_search_type("model") == "model"

    def test_single_valid_string_dataset(self) -> None:
        assert _normalize_search_type("dataset") == "dataset"

    def test_single_valid_string_space(self) -> None:
        assert _normalize_search_type("space") == "space"

    def test_single_valid_string_user(self) -> None:
        assert _normalize_search_type("user") == "user"

    def test_single_valid_string_org(self) -> None:
        assert _normalize_search_type("org") == "org"

    def test_list_two_items_returns_comma_separated(self) -> None:
        assert _normalize_search_type(["model", "dataset"]) == "model,dataset"

    def test_list_single_item(self) -> None:
        assert _normalize_search_type(["space"]) == "space"

    def test_list_three_items(self) -> None:
        assert _normalize_search_type(["model", "dataset", "space"]) == "model,dataset,space"

    def test_invalid_string_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid search_type"):
            _normalize_search_type("invalid")

    def test_invalid_type_in_list_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Invalid search_type"):
            _normalize_search_type(["model", "notatype"])


# ---------------------------------------------------------------------------
# _build_filters_html
# ---------------------------------------------------------------------------


class TestBuildFiltersHtml:
    def test_single_type_returns_empty_string(self) -> None:
        assert _build_filters_html("model") == ""

    def test_all_returns_five_chips(self) -> None:
        html = _build_filters_html("all")
        assert html.count("hf-search-filter-chip") == 5

    def test_two_types_returns_two_chips(self) -> None:
        html = _build_filters_html("model,dataset")
        assert html.count("hf-search-filter-chip") == 2

    def test_three_types_returns_three_chips(self) -> None:
        html = _build_filters_html("model,dataset,space")
        assert html.count("hf-search-filter-chip") == 3

    def test_chips_contain_correct_data_types(self) -> None:
        html = _build_filters_html("model,space")
        assert 'data-type="model"' in html
        assert 'data-type="space"' in html
        assert 'data-type="dataset"' not in html

    def test_chips_follow_category_order_regardless_of_input_order(self) -> None:
        # Input order reversed — output must follow _CATEGORY_ORDER (model before space)
        html = _build_filters_html("space,model")
        assert html.index('data-type="model"') < html.index('data-type="space"')

    def test_chips_have_active_class_by_default(self) -> None:
        html = _build_filters_html("model,dataset")
        assert html.count('"hf-search-filter-chip active"') == 2


# ---------------------------------------------------------------------------
# result_limit validation
# ---------------------------------------------------------------------------


class TestResultLimit:
    def test_default_is_five(self) -> None:
        assert _RESULT_LIMIT_DEFAULT == 5

    def test_max_is_twenty(self) -> None:
        assert _RESULT_LIMIT_MAX == 20

    def test_default_accepted(self) -> None:
        HuggingFaceHubSearch()  # should not raise

    def test_boundary_min(self) -> None:
        HuggingFaceHubSearch(result_limit=1)  # should not raise

    def test_boundary_max(self) -> None:
        HuggingFaceHubSearch(result_limit=20)  # should not raise

    def test_mid_value(self) -> None:
        HuggingFaceHubSearch(result_limit=10)  # should not raise

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="result_limit"):
            HuggingFaceHubSearch(result_limit=0)

    def test_above_max_raises(self) -> None:
        with pytest.raises(ValueError, match="result_limit"):
            HuggingFaceHubSearch(result_limit=21)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="result_limit"):
            HuggingFaceHubSearch(result_limit=-1)

    def test_string_raises(self) -> None:
        with pytest.raises(ValueError, match="result_limit"):
            HuggingFaceHubSearch(result_limit="10")  # type: ignore[arg-type]

    def test_float_raises(self) -> None:
        with pytest.raises(ValueError, match="result_limit"):
            HuggingFaceHubSearch(result_limit=5.0)  # type: ignore[arg-type]

    def test_error_message_contains_max(self) -> None:
        with pytest.raises(ValueError, match=str(_RESULT_LIMIT_MAX)):
            HuggingFaceHubSearch(result_limit=99)


# ---------------------------------------------------------------------------
# preprocess
# ---------------------------------------------------------------------------


class TestPreprocess:
    @pytest.fixture
    def component(self) -> HuggingFaceHubSearch:
        return HuggingFaceHubSearch()

    def test_none_returns_none(self, component: HuggingFaceHubSearch) -> None:
        assert component.preprocess(None) is None

    def test_empty_string_returns_none(self, component: HuggingFaceHubSearch) -> None:
        assert component.preprocess("") is None

    def test_json_string_returns_dict(self, component: HuggingFaceHubSearch) -> None:
        payload = {"id": "bert-base", "type": "model", "url": "https://huggingface.co/bert-base"}
        result = component.preprocess(json.dumps(payload))
        assert result == payload

    def test_plain_string_wraps_as_minimal_dict(self, component: HuggingFaceHubSearch) -> None:
        result = component.preprocess("bert-base")
        assert result == {"id": "bert-base", "type": None, "url": None}

    def test_invalid_json_falls_back_to_plain_string(self, component: HuggingFaceHubSearch) -> None:
        result = component.preprocess("{not valid json}")
        assert result == {"id": "{not valid json}", "type": None, "url": None}


# ---------------------------------------------------------------------------
# postprocess
# ---------------------------------------------------------------------------


class TestPostprocess:
    @pytest.fixture
    def component(self) -> HuggingFaceHubSearch:
        return HuggingFaceHubSearch()

    def test_none_returns_none(self, component: HuggingFaceHubSearch) -> None:
        assert component.postprocess(None) is None

    def test_dict_with_id_returns_id_string(self, component: HuggingFaceHubSearch) -> None:
        result = component.postprocess({"id": "bert-base", "type": "model"})
        assert result == "bert-base"

    def test_dict_without_id_returns_none(self, component: HuggingFaceHubSearch) -> None:
        result = component.postprocess({"type": "model"})
        assert result is None

    def test_plain_string_returns_same_string(self, component: HuggingFaceHubSearch) -> None:
        result = component.postprocess("bert-base")
        assert result == "bert-base"


# ---------------------------------------------------------------------------
# api_info
# ---------------------------------------------------------------------------


class TestApiInfo:
    @pytest.fixture
    def component(self) -> HuggingFaceHubSearch:
        return HuggingFaceHubSearch()

    def test_returns_object_type(self, component: HuggingFaceHubSearch) -> None:
        info = component.api_info()
        assert info["type"] == "object"

    def test_has_id_string_property(self, component: HuggingFaceHubSearch) -> None:
        info = component.api_info()
        assert "id" in info["properties"]
        assert info["properties"]["id"]["type"] == "string"

    def test_has_type_property(self, component: HuggingFaceHubSearch) -> None:
        info = component.api_info()
        assert "type" in info["properties"]

    def test_has_url_property(self, component: HuggingFaceHubSearch) -> None:
        info = component.api_info()
        assert "url" in info["properties"]

    def test_has_description(self, component: HuggingFaceHubSearch) -> None:
        info = component.api_info()
        assert "description" in info
        assert isinstance(info["description"], str)
        assert len(info["description"]) > 0
