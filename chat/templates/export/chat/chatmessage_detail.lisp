  (message
   :time {{ object.timestamp|date:"U" }} :timezone "{{ object.timestamp|date:"O" }}"{% comment %}"{% endcomment %}
   :author {% include "export/auth/user.lisp" with object=object.author only %} :authenticity nil
   :unicode {% with points=object.get_body_codepoints %}{% comment %}
    {% endcomment %}{% if points %}(list{% comment %}
     {% endcomment %}{% if points|length < 16 %}{% for point in points %} point{% endfor %}){% comment %}
     {% endcomment %}{% else %}{% for point in points %} {{ point }}{% if forloop.counter|divisibleby:"16" %}
   {% endif %}{% endfor %}
   ){% endif %}{% else %}nil{% endif %}{% endwith %}
   :id {{ object.id }}
  )
