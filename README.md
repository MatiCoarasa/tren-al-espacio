## Build web version

```python
python -m pygbag --build main.py
cd build
python -m http.server 8000
```