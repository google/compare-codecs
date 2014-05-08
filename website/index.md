---
layout: default
title: Your New Jekyll Site
---

### What is This?

Good question.


### Recent Comparisons

<div class="well well-sm" style="font-style: italic;">
**LQ:** A codec comparison run is similar to a blog post -- in that it's
atomic, temporal and has metadata. Maybe Jekyll's "blog-awareness" can be adapted to organizing results.
</div>

<ul class="posts">
  {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>
