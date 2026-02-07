{{ name | escape | underline }}

.. currentmodule:: {{ module }}

.. autoclass:: {{ name }}
   :members:
   :undoc-members:
   :show-inheritance:
   {# 注意：这里删除了 :inherited-members: #}

   {% block methods %}
   {% if methods %}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
      :nosignatures:
   {% for item in methods %}
      {# 核心过滤逻辑：仅当方法是在当前类中定义时才显示 #}
      {%- if item not in inherited_members or item == '__init__' %}
         ~{{ name }}.{{ item }}
      {%- endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
      {%- if item not in inherited_members %}
         ~{{ name }}.{{ item }}
      {%- endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}