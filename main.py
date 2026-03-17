from my_functions import *
import time
import os
import sys

source = 'demo_helmet2.mp4'

save_video = True  # want to save video? (when video as source)
show_video = True  # set true when using video file
save_img = False  # set true when using only image file to save the image
max_images_to_save = 20  # Define the maximum number of images to save per iteration
max_duration_seconds = 5  # Maximum duration to run in seconds

# saving video as output
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, frame_size)

cap = cv2.VideoCapture(source)

images_saved_count = 0  # Counter to keep track of the number of images saved
frame_count = 0  # Add frame counter for debugging

# Create directories if they don't exist
os.makedirs('number_plates', exist_ok=True)
os.makedirs('riders_pictures', exist_ok=True)

# Record start time
start_time = time.time()
elapsed_time = 0

print(f"Starting processing. Will run for maximum {max_duration_seconds} seconds or save {max_images_to_save} images")

while cap.isOpened() and elapsed_time < max_duration_seconds and images_saved_count < max_images_to_save:
    ret, frame = cap.read()
    
    # Check elapsed time
    elapsed_time = time.time() - start_time
    
    if ret:
        frame_count += 1
        frame = cv2.resize(frame, frame_size)  # resizing image
        original_frame = frame.copy()
        frame, results = object_detection(frame)

        rider_list = []
        head_list = []
        number_list = []

        for result in results:
            x1, y1, x2, y2, cnf, clas = result
            if clas == 0:
                rider_list.append(result)
            elif clas == 1:
                head_list.append(result)
            elif clas == 2:
                number_list.append(result)

        # Only print detection info occasionally to avoid console spam
        if frame_count % 30 == 0:
            print(f"\n--- Frame {frame_count} | Time: {elapsed_time:.1f}s | Images saved: {images_saved_count} ---")
            print(f"Found {len(rider_list)} riders, {len(head_list)} heads, {len(number_list)} number plates")

        for rider in rider_list:
            time_stamp = str(time.time())
            x1r, y1r, x2r, y2r, cnfr, clasr = rider
            helmet_absent = False
            rider_heads_found = 0

            for head in head_list:
                x1h, y1h, x2h, y2h, cnfh, clash = head

                if inside_box([x1r, y1r, x2r, y2r], [x1h, y1h, x2h, y2h]):
                    rider_heads_found += 1
                    
                    try:
                        head_img = original_frame[y1h:y2h, x1h:x2h]
                        if head_img.size == 0:
                            continue
                            
                        helmet_present = img_classify(head_img)
                        
                    except Exception as e:
                        print(f'Error in processing head image: {e}')
                        continue

                    # Check if helmet is present (not None and True)
                    is_helmet_present = helmet_present[0] is True
                    
                    # For visualization
                    if helmet_present[0] is not None:
                        color = (0, 255, 0) if helmet_present[0] else (0, 0, 255)
                    else:
                        color = (0, 0, 255)  # Default to red for None (assuming no helmet)
                        
                    frame = cv2.rectangle(frame, (x1h, y1h), (x2h, y2h), color, 1)
                    
                    # Display confidence score
                    conf_text = f'{round(helmet_present[1], 1)}'
                    if helmet_present[0] is None:
                        conf_text = f'No helmet? {conf_text}'
                        
                    frame = cv2.putText(frame, conf_text, (x1h, y1h + 40),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

                    # Consider None as helmet absent (or adjust based on your needs)
                    if not is_helmet_present:  # This will be True when helmet_present[0] is None or False
                        helmet_absent = True
                        
                        # Save number plate immediately when helmet is absent
                        if images_saved_count < max_images_to_save:
                            number_plate_saved = False
                            
                            # Check all number plates for this rider
                            for num in number_list:
                                x1_num, y1_num, x2_num, y2_num, conf_num, clas_num = num
                                
                                if inside_box([x1r, y1r, x2r, y2r], [x1_num, y1_num, x2_num, y2_num]):
                                    try:
                                        # Validate coordinates
                                        if (y1_num >= 0 and x1_num >= 0 and 
                                            y2_num <= original_frame.shape[0] and 
                                            x2_num <= original_frame.shape[1]):
                                            
                                            num_img = original_frame[y1_num:y2_num, x1_num:x2_num]
                                            if num_img.size > 0:
                                                # Save number plate
                                                filename = f'number_plates/{time_stamp}_{conf_num:.2f}.jpg'
                                                cv2.imwrite(filename, num_img)
                                                print(f'Number plate saved: {filename}')
                                                number_plate_saved = True
                                                images_saved_count += 1
                                                break
                                    except Exception as e:
                                        print(f'Error saving number plate: {e}')
                            
                            # If no number plate found, save rider as fallback
                            if not number_plate_saved:
                                try:
                                    filename = f'riders_pictures/rider_{time_stamp}_no_helmet.jpg'
                                    cv2.imwrite(filename, original_frame[y1r:y2r, x1r:x2r])
                                    print(f'Rider image saved (no number plate): {filename}')
                                    images_saved_count += 1
                                except Exception as e:
                                    print(f'Error saving rider: {e}')

        if save_video:
            out.write(frame)
        if save_img:
            cv2.imwrite('saved_frame.jpg', frame)
        if show_video:
            display_frame = cv2.resize(frame, (900, 450))
            cv2.imshow('Frame', display_frame)

        # Check for 'q' key press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("User requested stop")
            break
            
        # Check if we've reached the time limit or image limit
        if images_saved_count >= max_images_to_save:
            print(f"Reached maximum images to save: {images_saved_count}")
            break
            
        if elapsed_time >= max_duration_seconds:
            print(f"Reached maximum duration: {max_duration_seconds} seconds")
            break

    else:
        # No more frames in video
        print("End of video reached")
        break

# Add a countdown before closing
print(f"\nProcessing stopped. Closing in 5 seconds...")
print(f"Final stats: {frame_count} frames processed, {images_saved_count} images saved in {time.time()-start_time:.1f} seconds")

# Countdown
for i in range(5, 0, -1):
    print(f"Closing in {i}...")
    cv2.waitKey(1000)  # Wait 1 second

# Clean up
cap.release()
if save_video:
    out.release()
cv2.destroyAllWindows()

print(f'Execution completed. Total images saved: {images_saved_count}')