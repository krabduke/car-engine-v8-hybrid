/* The air inside the engine.
 *
 * Not a solver: the gas path through a piston engine is a known duct, and the
 * model already knows where it runs -- engine/gaspath.py defines the
 * centrelines that plumbing.py builds the runners and primaries along, and
 * writes them into the manifest. So this draws the air going down the pipes
 * that are actually there, rather than a plausible-looking guess at them.
 *
 * What makes it worth watching is the valve timing. Each cylinder's induction
 * only flows while its intake valve is open and its exhaust only while the
 * exhaust valve is open, both taken from the cam in spec.CAM, and each
 * cylinder is offset by its place in the firing order. Run it and the
 * breathing travels down the engine in firing order -- 1, 8, 3, 6, 4, 5, 2, 7
 * -- which is the thing a cutaway drawing can never show you.
 */

const MM = 0.001;

/* Model millimetres to scene metres. Blender (x, y, z) with z up becomes
   three.js (x, z, -y); the root's own transform does the centring. */
function toScene(THREE, p) {
  return new THREE.Vector3(p[0] * MM, p[2] * MM, -p[1] * MM);
}

const VERT = `
  varying float vArc;
  varying float vRim;
  attribute float aArc;
  void main(){
    vArc = aArc;
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vec3 n = normalize(normalMatrix * normal);
    // brighter round the silhouette, so a tube reads as a tube and not a bar
    vRim = 1.0 - abs(dot(n, normalize(-mv.xyz)));
    gl_Position = projectionMatrix * mv;
  }
`;

const FRAG = `
  precision highp float;
  uniform vec3  uA, uB;
  uniform float uTime, uGate, uSpeed, uDensity, uOpacity;
  varying float vArc;
  varying float vRim;
  void main(){
    // a train of soft slugs travelling along the duct
    float ph = fract(vArc * uDensity - uTime * uSpeed);
    float slug = smoothstep(0.0, 0.18, ph) * (1.0 - smoothstep(0.30, 0.92, ph));
    vec3 col = mix(uA, uB, clamp(vArc, 0.0, 1.0));
    float a = uOpacity * uGate * (0.28 + 0.72 * slug);
    a *= 0.55 + 0.45 * vRim;
    if(a < 0.004) discard;
    gl_FragColor = vec4(col * (0.75 + 0.55 * slug), a);
  }
`;

function tube(THREE, pts, radius, radial) {
  const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal', 0.5);
  const seg = Math.max(24, pts.length * 14);
  const g = new THREE.TubeGeometry(curve, seg, radius, radial, false);
  // arc length along the tube, 0 at the inlet and 1 at the outlet, so the
  // slugs travel the right way and the colour ramp follows the gas
  const pos = g.attributes.position;
  const arc = new Float32Array(pos.count);
  for (let i = 0; i < pos.count; i++) {
    arc[i] = Math.floor(i / (radial + 1)) / seg;
  }
  g.setAttribute('aArc', new THREE.BufferAttribute(arc, 1));
  return g;
}

export class GasFlow {
  constructor(THREE, root, gas) {
    this.THREE = THREE;
    this.gas = gas;
    this.group = new THREE.Group();
    this.group.name = 'gasflow';
    this.group.visible = false;
    root.add(this.group);
    this.runs = [];
    this.phase = 0;
    this.clock = 0;
    this._build();
  }

  _run(pts, radius, a, b, opts = {}) {
    const THREE = this.THREE;
    const v = pts.map(p => toScene(THREE, p));
    const mat = new THREE.ShaderMaterial({
      uniforms: {
        uA: {value: new THREE.Color(a)},
        uB: {value: new THREE.Color(b)},
        uTime: {value: 0}, uGate: {value: 1},
        uSpeed: {value: opts.speed || 0.55},
        uDensity: {value: opts.density || 3.0},
        uOpacity: {value: opts.opacity || 0.95},
      },
      vertexShader: VERT, fragmentShader: FRAG,
      transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    });
    const m = new THREE.Mesh(tube(THREE, v, radius * MM, 12), mat);
    m.renderOrder = 3;
    this.group.add(m);
    const run = {mesh: m, mat, ...opts};
    this.runs.push(run);
    return run;
  }

  _build() {
    const g = this.gas;
    // Colour is the state of the gas, not decoration: cold charge in, hot
    // gas out, and the charge warmed by the compressor then cooled again.
    //
    // Radii are deliberately well under the ducts they run in. A stream drawn
    // at the bore of its own pipe fills the picture and you lose the engine
    // behind it -- the point is to see the air THROUGH the hardware, so the
    // air has to leave room for the hardware.
    for (const c of g.cylinders) {
      this._run(c.intake, 7.0, '#63A9D6', '#9FD2EC',
                {kind: 'intake', phase: c.phase, speed: 0.75, density: 2.4});
      this._run(c.chamber, 9.0, '#FFD9A0', '#FF7A3C',
                {kind: 'burn', phase: c.phase, speed: 0.30, density: 1.2,
                 opacity: 0.9});
      this._run(c.exhaust, 7.5, '#FF7A34', '#B8331C',
                {kind: 'exhaust', phase: c.phase, speed: 0.95, density: 2.0});
    }
    // the boost loop runs continuously -- it is not gated by any one valve
    for (const p of g.boost) {
      this._run(p, 11.0, '#E8A860', '#7FBEDD',
                {kind: 'boost', speed: 0.45, density: 1.6, opacity: 0.8});
    }
    for (const p of g.tailpipe) {
      this._run(p, 13.0, '#B0472F', '#6E5B55',
                {kind: 'tail', speed: 0.7, density: 1.4, opacity: 0.75});
    }
  }

  /* Is a window [open, close) in a 720 degree cycle covering this phase?
     Handles the wrap, which both windows do here -- the intake closes at 604
     and the exhaust at 388 after opening at 116. */
  static _open(phase, win) {
    const [o, c] = win;
    return o <= c ? (phase >= o && phase < c) : (phase >= o || phase < c);
  }

  setPhase(deg720) {
    this.phase = ((deg720 % 720) + 720) % 720;
    const T = this.gas.timing;
    for (const r of this.runs) {
      if (r.kind === 'boost' || r.kind === 'tail') { r.mat.uniforms.uGate.value = 1; continue; }
      const p = ((this.phase - r.phase) % 720 + 720) % 720;
      if (r.kind === 'intake') {
        r.mat.uniforms.uGate.value = GasFlow._open(p, T.intake) ? 1 : 0;
      } else if (r.kind === 'exhaust') {
        r.mat.uniforms.uGate.value = GasFlow._open(p, T.exhaust) ? 1 : 0;
      } else {
        // the chamber lights at the top of the power stroke and fades
        const f = p < 90 ? 1 - p / 90 : 0;
        r.mat.uniforms.uGate.value = f * f;
      }
    }
  }

  tick(dt) {
    if (!this.group.visible) return;
    this.clock += dt;
    for (const r of this.runs) r.mat.uniforms.uTime.value = this.clock;
  }

  setVisible(on) { this.group.visible = !!on; }

  dispose() {
    for (const r of this.runs) { r.mesh.geometry.dispose(); r.mat.dispose(); }
    this.group.clear();
    this.runs = [];
  }
}
