1. **Add `Layer` enum in `models.py`**
   - Create an enum `Layer` with values `UI`, `CLIENT`, `SERVICE`, and `CROSS_LAYER`.
2. **Update `Prompt` dataclass in `models.py`**
   - Add a field `layer: Optional[Layer] = None` to `Prompt`.
   - Add fields for UI details: `ui_details: Optional[str] = None`, `affected_view: Optional[str] = None`, `state_transition: Optional[str] = None`.
   - Add fields for client/service details: `client_details: Optional[str] = None`, `service_details: Optional[str] = None`, `boundary_details: Optional[str] = None`, `route: Optional[str] = None`, `contract: Optional[str] = None`.
   - Implement `__post_init__` method in `Prompt` to automatically append "Verify both caller and callee behavior" to `acceptance_criteria` when `layer` is `Layer.CROSS_LAYER`.
3. **Update `tests/test_models.py`**
   - Add tests for `Layer` enum.
   - Add tests for `Prompt` with cross-layer behavior.
4. **Update analyzers / perspectives if needed**
   - Ensure the new logic can be used in `organism.py` and `diagnostics.py` or `perspectives.py` where prompts are generated (based on further checks). Wait, let me check where prompts are generated first.
