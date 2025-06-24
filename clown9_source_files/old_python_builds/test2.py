import python_a2s  # Explicitly use "python_a2s"
info = python_a2s.query_info(('79.127.217.197', 22912))
print(info.map_name)