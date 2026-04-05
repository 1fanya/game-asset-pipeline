; GIMP Script-Fu: Animation Frame Processor for rotation_effect
; Usage: gimp -i -b '(script-fu-load "output/scripts/gimp/anim_rotation_effect.scm")' -b '(gimp-quit 0)'
(define (process-animation-rotation_effect output-dir frame-count)
  (let loop ((i 0))
    (when (< i frame-count)
      (let* (
        (img (car (gimp-image-new 128 128 RGB)))
        (layer (car (gimp-layer-new img 128 128 RGBA-IMAGE
                (string-append "frame_" (number->string i)) 100 LAYER-MODE-NORMAL)))
      )
      (gimp-image-insert-layer img layer 0 -1)

      ; Apply rotation transform for this frame
      (gimp-item-transform-rotate-default layer
        (* (/ (* 2 3.14159) frame-count) i) TRUE 0 0)

      ; Apply color overlay
      (gimp-context-set-foreground '(0 200 220))
      (gimp-edit-fill layer FILL-FOREGROUND)

      ; Export frame
      (file-png-save RUN-NONINTERACTIVE img layer
        (string-append output-dir "/frame_" (number->string i) ".png")
        (string-append "frame_" (number->string i))
        0 9 1 1 1 1 1)

      (gimp-image-delete img)
      (loop (+ i 1))))))

(process-animation-rotation_effect "output/animations/rotation_effect" 8)
