  (message
   :time {{ object.timestamp|date:"U" }} :timezone "{{ object.timestamp|date:"O" }}"{% comment %}"{% endcomment %}
   :author {% include "export/auth/user.lisp" with object=object.author only %}   :authenticity nil
   :unicode {% with points=object.get_body_codepoints %}{% if points %}(list{% if points|length < 16 %} {% for point in points %}{{ point }}{% if not forloop.last %} {% endif %}{% endfor %}){% else %}
    {% for point in points %}{{ point }}{% if forloop.counter|divisibleby:"16" and not forloop.last%}
   {% endif %}{% if not forloop.last %} {% endif %}{% endfor %}
   ){% endif %}{% else %}nil{% endif %}{% endwith %}
   :id {{ object.id }}
  )
