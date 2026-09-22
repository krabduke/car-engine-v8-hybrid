BLENDER := /Applications/Blender.app/Contents/MacOS/Blender
BLEND   := build/engine.blend
SAMPLES ?= 128

.PHONY: all build verify render export stl manifest viewer clean

all: build verify render export

build:
	$(BLENDER) --background --python engine/assemble.py
	python3 tools/make_manifest.py

verify:
	python3 engine/verify.py
	python3 tools/audit_structure.py
	python3 tools/audit_geometry.py
	python3 tools/audit_watertight.py
	python3 tools/audit_intersect.py
	python3 tools/audit_joints.py
	python3 tools/audit_support.py
	python3 tools/audit_clearance.py
	python3 tools/audit_manifest.py
	python3 tools/check_vendor.py
	node tools/validate_viewer.mjs .

render:
	$(BLENDER) -b $(BLEND) -P engine/render.py -- all $(SAMPLES)

export:
	$(BLENDER) -b $(BLEND) -P engine/export.py -- glb

stl:
	$(BLENDER) -b $(BLEND) -P engine/export.py -- stl

manifest:
	python3 tools/make_manifest.py

viewer:
	@echo "Serving http://localhost:8790/viewer/ - Ctrl-C to stop"
	@python3 -m http.server 8790 --bind 127.0.0.1

clean:
	rm -rf build renders
