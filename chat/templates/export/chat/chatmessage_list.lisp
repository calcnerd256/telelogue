(telelogue{% if is_paginated %}
 :paginate (
  pagination
  :page {{ page_obj.number }}
  :of {{ page_obj.paginator.num_pages }}
 ){% endif %}
 :messages (
  list
{% for object in object_list %}{% include "export/chat/chatmessage_detail.lisp" %}{% endfor %} )
 :server nil
)
