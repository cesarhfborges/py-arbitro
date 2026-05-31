import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

_model = None

def get_yolo_model():
    global _model
    if YOLO is None:
        return None
    if _model is None:
        # Load model. It will auto-download yolov8n-seg.pt to the working directory if not found.
        _model = YOLO("yolov8n-seg.pt")
    return _model

def get_player_polygons(image_np):
    """
    Receives an image as a numpy array (BGR or RGB).
    Returns a list of polygons (each polygon is a list of (x, y) tuples) for all detected persons.
    """
    polygons_out = []
    model = get_yolo_model()
    
    if model is None or image_np is None:
        return polygons_out
        
    # Run inference. verbose=False disables the print outputs per image.
    results = model(image_np, verbose=False)
    
    if not results or not results[0].masks:
        return polygons_out
        
    result = results[0]
    boxes = result.boxes
    masks = result.masks
    
    if boxes is None or masks is None:
        return polygons_out
        
    classes = boxes.cls.cpu().numpy()
    polygons = masks.xy # List of numpy arrays, each is Nx2
    
    for cls_id, poly in zip(classes, polygons):
        if int(cls_id) == 0: # 0 is person in COCO dataset
            if len(poly) > 2:
                poly_list = []
                for pt in poly:
                    poly_list.append((float(pt[0]), float(pt[1])))
                polygons_out.append(poly_list)
                
    return polygons_out
