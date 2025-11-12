import argparse, os, re
from unrealcv import Client

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    ap.add_argument('--x', type=float, required=True)
    ap.add_argument('--y', type=float, required=True)
    ap.add_argument('--z', type=float, required=True)
    ap.add_argument('--target_x', type=float, default=None)
    ap.add_argument('--target_y', type=float, default=None)
    ap.add_argument('--target_z', type=float, default=None)
    ap.add_argument('--yaw', type=float, default=None)
    ap.add_argument('--pitch', type=float, default=None)
    ap.add_argument('--roll', type=float, default=None)
    ap.add_argument('--fov', type=float, default=90.0)
    ap.add_argument('--width', type=int, default=640)
    ap.add_argument('--height', type=int, default=480)
    ap.add_argument('--out', default='shot.png')
    ap.add_argument('--save_dir', default='C:/Users/BenF/Pictures/ue_cv')
    args = ap.parse_args()

    os.makedirs(args.save_dir, exist_ok=True)
    out_path = os.path.join(args.save_dir, args.out).replace('\\', '/')

    client = Client((args.host, args.port))
    client.connect()
    if not client.isconnected():
        raise SystemExit('Could not connect to UnrealCV server')

    def ok(resp: str) -> bool:
        return resp and not resp.lower().startswith('error')

    def req(cmd: str) -> str:
        resp = client.request(cmd)
        print(f'>> {cmd} -> {resp[:120]}')
        return resp

    # ---- Camera discovery: prefer numeric IDs ----
    cams = req('vget /cameras') or ''
    numeric_ids = re.findall(r'\b\d+\b', cams)
    if numeric_ids:
        cam_id = numeric_ids[0]
    else:
        # many UE5 builds still have a default camera id 0 even if not listed cleanly
        cam_id = '0'
    print(f'Using numeric camera id: {cam_id}')

    # ---- Try viewmode globally (per-camera often unsupported on UE5) ----
    if not ok(req('vset /viewmode lit')):
        print('Non-fatal: global viewmode not supported, continuing.')

    # ---- Try pose/FOV/size only if handlers exist in your build ----
    for cmd in [
        f'vset /camera/{cam_id}/size {args.width} {args.height}',
        f'vset /camera/{cam_id}/fov {args.fov}',
        f'vset /camera/{cam_id}/location {args.x} {args.y} {args.z}',
    ]:
        resp = req(cmd)
        if not ok(resp):
            print(f'Ignored (unsupported): {cmd}')

    if args.target_x is not None and args.target_y is not None and args.target_z is not None:
        resp = req(f'vset /camera/{cam_id}/lookat {args.target_x} {args.target_y} {args.target_z}')
        if not ok(resp):
            print('Ignored (unsupported): lookat')
    elif args.yaw is not None and args.pitch is not None and args.roll is not None:
        resp = req(f'vset /camera/{cam_id}/rotation {args.yaw} {args.pitch} {args.roll}')
        if not ok(resp):
            print('Ignored (unsupported): rotation')

    # ---- Capture attempts (ordered) ----
    attempts = [
        f'vget /camera/{cam_id}/lit {out_path}',
        f'vget /camera/0/lit {out_path}', 
        f'vget /screenshot {out_path}', 
    ]
    for cmd in attempts:
        if ok(req(cmd)):
            print('Saved to:', out_path)
            return

    raise SystemExit('Capture failed: no supported capture URI found')

if __name__ == '__main__':
    main()
