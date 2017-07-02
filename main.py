# conding: utf-8
# convertisseur de maps tiled vers le format d'unamed
# copytight Folaefolc (alias Loodoor), tous droits réservés
import glob
import time
from xml.etree import ElementTree as ET
import os


LOG = []


def log(*args):
    LOG.append('[{}] {}'.format(time.strftime('%H:%M:%S'), ' '.join(str(a) for a in args)))


def convert_file(filename):
    tree = ET.parse(filename)
    log("starting to convert {}".format(filename))
    
    root = tree.getroot()
    log(root.attrib)
    
    w, h = 0, 0
    
    try:
        w, h = int(root.attrib['width']), int(root.attrib['height'])
    except ValueError:
        log("can not get the correct width or height in {}. aborting".format(filename))
        return None
    
    layers = {}
    objects = []
    
    for child in root:
        if child.tag == 'layer':
            try:
                Lw, Lh = int(child.attrib['width']), int(child.attrib['height'])
            except ValueError:
                log("can not get the correct width or height of layer {} in {}. aborting".format(child.attrib['name'], filename))
                return None
            else:
                if w != Lw or h != Lh:
                    log("bad configuration of layer {} in {}. aborting".format(child.attrib['name'], filename))
                    return None
                else:
                    t = {child.attrib['name']: []}
                    # getting layer>data>`content`
                    c = child[0].text.split('\n')
                    for line in c:
                        t[child.attrib['name']].append(line.split(','))
                        for i, e in enumerate(t[child.attrib['name']][-1]):
                            try:
                                if e != '':
                                    t[child.attrib['name']][-1][i] = int(e)
                            except ValueError:
                                log("can not convert tile descriptor '{}' to a correct integer in {}, {}. aborting".format(e, child.attrib['name'], filename))
                                return None
                    layers.update(t)
                    log("adding layer {} to layers, on map {}".format(child.attrib['name'], filename))
        elif child.tag == 'objectgroup':
            if child.attrib['name'] != 'calque5':
                log("object group is not configured correctly in {}. aborting".format(filename))
                return None
            else:
                for c in child:
                    if c.tag == 'object':
                        try:
                            x, y = int(c.attrib['x']), int(c.attrib['y'])
                        except ValueError:
                            log("can not convert tp position to corrects integers ({}) in {}. aborting".format(c.attrib['id'], filename))
                            return None
                        
                        if c.attrib['width'] != c.attrib['height'] != '16':
                            log("tp {} in {} misconfigured. aborting".format(c.attrib['id'], filename))
                            return None
                        
                        x_dest, y_dest, dest_map_id = 0, 0, 0
                        
                        for p in c[0]:
                            if p.tag == 'property':
                                for k, v in p.attrib.items():
                                    if k == 'name':
                                        if v == 'x_dest':
                                            try:
                                                x_dest = int(p.attrib['value'])
                                            except ValueError:
                                                log("can not convert x_dest in tp {} to a correct integer value, in {}. aborting".format(c.attrib['id'], filename))
                                                return None
                                        elif v == 'y_dest':
                                            try:
                                                y_dest = int(p.attrib['value'])
                                            except ValueError:
                                                log("can not convert y_dest in tp {} to a correct integer value, in {}. aborting".format(c.attrib['id'], filename))
                                                return None
                                        elif v == 'dest_map_id':
                                            try:
                                                dest_map_id = int(p.attrib['value'])
                                            except ValueError:
                                                log("can not convert dest_map_id in tp {} to a correct integer value, in {}. aborting".format(c.attrib['id'], filename))
                                                return None
                                    elif k == 'type' or k == 'value':
                                        pass
                                    else:
                                        log("found an unrecognizable property : {} in tp {}, in {}. aborting".format(k, c.attrib['id'], filename))
                                        return None
                            else:
                                log('found an unrecognizable tag in properties of tp {} : {}, in {}. aborting'.format(c.attrib['id'], p.tag, filename))
                                return None
                        
                        objects.append({
                            c.attrib["id"]: [
                                dest_map_id,                    # on map
                                (x // 16) + (y // 16) * w,      # on case
                                x_dest,                         # to case x
                                y_dest                          # to case y
                            ]
                        })
                    else:
                        log('found an unrecognizable tag in objectgroup : {}, in {}. aborting'.format(c.tag, filename))
                        return None
        elif child.tag == 'tileset':
            pass
        else:
            log("found an unrecognizable tag : {}, in {}. aborting".format(child.tag, filename))
            return None
    
    log("starting to process extracted data in {}".format(filename))
    fname = os.path.dirname(filename) + 'out/' + os.path.basename(filename).split('.')[0] + '.umd'
    if not os.path.exists(os.path.dirname(filename) + 'out/'):
        os.mkdir(os.path.dirname(filename) + 'out/')
    
    ret = {
        "tp": [],
        "map3": [],
        "map2": [],
        "map": [],
        "width": w,
        "height": h,
        "filename": fname
    }
    
    log("parsing tp in {}".format(filename))
    for e in objects:
        for v in e.values():
            ret["tp"].append({
                "tomap": v[0],
                "oncase": v[1],
                "tocasex": v[2],
                "tocasey": v[3]
            })
    
    log("parsing layers in {}".format(filename))
    for n, lay in layers.items():
        if n == "calque1":
            o = []
            for line in lay:
                for e in line:
                    if e:
                        try:
                            n = int(e)
                            n -= 1
                        except ValueError:
                            log("can not convert {} to a valid integer in object layer in {}.aborting".format(e, filename))
                            return None
                        o.append({
                            "colliding": False,
                            "id": n
                        })
            ret["map"] = o
        elif n == "calque2":   # colliding layer in Unamed !
            o = []
            for i, line in enumerate(lay):    # i = y
                for k, e in enumerate(line):  # k = x
                    if e:
                        try:
                            n = int(e)
                            n -= 1
                        except ValueError:
                            log("can not convert {} to a valid integer in object layer in {}.aborting".format(e, filename))
                            return None
                        o.append({
                            "colliding": (layers["calque4"][i][k] != 0),
                            "id": n
                        })
            ret["map2"] = o
        elif n == "calque3":
            o = []
            for line in lay:
                for e in line:
                    if e:
                        try:
                            n = int(e)
                            n -= 1
                        except ValueError:
                            log("can not convert {} to a valid integer in object layer in {}. aborting".format(e, filename))
                            return None
                        o.append({
                            "colliding": False,
                            "id": n
                        })
            ret["map3"] = o
    
    log("parsing of map in {} done".format(filename))
    
    return ret


def main():
    log("initialising")
    
    log("searching for .tmx files")
    files = glob.glob("maps/*.tmx")
    log("{} files found".format(len(files)))
    
    parsed = []
    for f in files:
        o = convert_file(f)
        if isinstance(o, dict):
            log("{} was correctly converted".format(f))
            parsed.append(o)
        else:
            log("{} couldn't be converted correctly ! aborting".format(f))
            return None
    
    # need to save parsed data
    for data in parsed:
        fname = data.pop("filename")
        with open(fname, "w") as file:
            file.write(str(data).replace('True', 'true').replace('False', 'false').replace('None', 'null'))
        log("saving map to {}".format(fname))
    
    log("done")


def save_logs():
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    with open('logs/log{}.txt'.format(time.strftime('%d_%m_%Y-%H_%M_%S')), "w") as file:
        file.write("\n".join(LOG))


if __name__ == '__main__':
    main()
    save_logs()