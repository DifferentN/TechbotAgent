import cv2
def crop(image,b):
    x=max(0,int(round(b.x)));y=max(0,int(round(b.y)))
    w=max(1,int(round(b.width)));h=max(1,int(round(b.height)))
    return image[y:y+h,x:x+w]

def resize_to(runtime_roi,design_roi):
    h,w=design_roi.shape[:2]
    return cv2.resize(runtime_roi,(w,h),interpolation=cv2.INTER_AREA)
