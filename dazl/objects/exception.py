

class NoParent(Exception):
    def __init__(self, obj):
        super().__init__(f"Object '{type(obj).__name__}' has no parent")


class NoParentAttribute(Exception):
    def __init__(self, parent, obj):
        super().__init__(f"Object '{type(obj).__name__}' with parent '{type(parent).__name__}' has no parent attribute")
