from my_functions import *

source = 0

save_video = True  # want to save video? (when video as source)
show_video = True  # set true when using video file
save_img = False  # set true when using only image file to save the image
max_images_to_save = 20  # Define the maximum number of images to save per iteration

# saving video as output
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, frame_size)

cap = cv2.VideoCapture(source)

images_saved_count = 0  # Counter to keep track of the number of images saved

while cap.isOpened():
    ret, frame = cap.read()

    if ret:
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

        for rider in rider_list:
            time_stamp = str(time.time())
            x1r, y1r, x2r, y2r, cnfr, clasr = rider
            helmet_absent = False  # Flag to track if helmet is absent for this rider

            for head in head_list:
                x1h, y1h, x2h, y2h, cnfh, clash = head

                if inside_box([x1r, y1r, x2r, y2r], [x1h, y1h, x2h, y2h]):  # if this head inside this rider bbox
                    try:
                        head_img = original_frame[y1h:y2h, x1h:x2h]
                        helmet_present = img_classify(head_img)
                    except Exception as e:
                        print(f'Error in processing head image: {e}')
                        continue

                    if helmet_present[0] is not None:
                        color = (0, 255, 0) if helmet_present[0] else (0, 0, 255)
                        frame = cv2.rectangle(frame, (x1h, y1h), (x2h, y2h), color, 1)
                        frame = cv2.putText(frame, f'{round(helmet_present[1], 1)}', (x1h, y1h + 40),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

                        if not helmet_present[0]:  # if helmet absent
                            helmet_absent = True  # Set flag to True when helmet is not present

            # Only save images if helmet is absent and we haven't exceeded max_images_to_save
            if helmet_absent and images_saved_count < max_images_to_save:
                try:
                    # Save rider image
                    cv2.imwrite(f'riders_pictures/{time_stamp}.jpg', original_frame[y1r:y2r, x1r:x2r])
                    print('Rider image saved successfully.')
                    images_saved_count += 1  # Increment the counter

                    # Save number plate for this rider
                    for num in number_list:
                        x1_num, y1_num, x2_num, y2_num, conf_num, clas_num = num
                        if inside_box([x1r, y1r, x2r, y2r], [x1_num, y1_num, x2_num, y2_num]):
                            try:
                                num_img = original_frame[y1_num:y2_num, x1_num:x2_num]
                                cv2.imwrite(f'number_plates/{time_stamp}_{conf_num}.jpg', num_img)
                                print('Number plate image saved successfully.')
                                # Don't increment counter again for number plate
                                # This way one rider counts as one save operation
                                break  # Only save first number plate per rider
                            except Exception as e:
                                print(f'Error in saving number plate image: {e}')

                except Exception as e:
                    print(f'Error in saving rider image: {e}')

        if save_video:  # save video
            out.write(frame)
        if save_img:  # save img
            cv2.imwrite('saved_frame.jpg', frame)
        if not show_video:
            pass
        else:  # show video
            frame = cv2.resize(frame, (900, 450))  # resizing to fit in the screen
            cv2.imshow('Frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q') or images_saved_count >= max_images_to_save:  # Exit condition when maximum images are saved
            break

    else:
        break

cap.release()
cv2.destroyAllWindows()
print('Execution completed')