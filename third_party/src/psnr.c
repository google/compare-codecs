/*
 ============================================================================
 Name        : psnr.c
 Copyright   : Copyright Google Inc, 2012.
 Description : Computes the overall/global PSNR of two input yuv clips.
 ============================================================================
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
#include <sys/stat.h>

#define MAX_PSNR 100

typedef enum {
  STATUS_OK              =  0,
  STATUS_USAGE_ERROR     = -1,
  STATUS_FILE_SIZE_ERROR = -2,
  STATUS_FILE_OPEN_ERROR = -3,
  STATUS_ARGS_ERROR      = -4,
  STATUS_ALLOC_ERROR     = -5,
} STATUS_CODE;


/* Note: Handles Maximum file size of 2GB! */
int get_file_size(const char *filename) {
  struct stat st;
  stat(filename, &st);
  return st.st_size;
}

double mse2psnr(double samples, double peak, double mse) {
  double psnr;

  if ((double)mse > 0.0)
    psnr = 10.0 * log10(peak * peak * samples / mse);
  else
    psnr = MAX_PSNR;      // Limit to prevent / 0

  if (psnr > MAX_PSNR)
    psnr = MAX_PSNR;

  return psnr;
}


int main(int argc, char *argv[]) {
  int i;
  int width, height;
  int frame_size;
  int max_frames;
  int number_of_frames = 0;
  double total_sq_error = 0.0;
  unsigned char *frame0 = NULL, *frame1 = NULL;
  FILE *file0_ptr = NULL, *file1_ptr = NULL;
  STATUS_CODE return_status = STATUS_OK;

  if (argc < 6) {
    fprintf (stderr, "Usage: %s <yuv_file1> <yuv_file2> "
             "<width> <height> <max_frames>\n", argv[0]);
    return_status = STATUS_USAGE_ERROR;
    goto end;
  }

  width  = strtol(argv[3], NULL, 10);
  height = strtol(argv[4], NULL, 10);
  if (width < 1 || height < 1) {
    fprintf (stderr, "ERROR: invalid frame size %dx%d.\n", width, height);
    return_status = STATUS_ARGS_ERROR;
    goto end;
  }

  frame_size = width * height * 3 / 2;
  {
    int size0 = get_file_size(argv[1]);
    int size1 = get_file_size(argv[2]);
    if ((size0 <= 0) || (size1 <= 0)) {
      fprintf(stderr, "ERROR: input file size exceeds 2GB limit.\n");
      return_status = STATUS_FILE_SIZE_ERROR;
      goto end;
    }

    if ((size0 != size1) || (size0 % frame_size)) {
      fprintf(stderr, "ERROR: input files must be same size and have only "
              "full frames (file sizes:%d, %d).\n", size0, size1);
      return_status = STATUS_FILE_SIZE_ERROR;
      goto end;
    }
  }

  if ((file0_ptr = fopen(argv[1], "rb")) == NULL) {
    fprintf (stderr, "ERROR: unable to open input file %s.\n", argv[1]);
    return_status = STATUS_FILE_OPEN_ERROR;
    goto end;
  }

  if ((file1_ptr = fopen(argv[2], "rb")) == NULL) {
    fprintf (stderr, "ERROR: unable to open input file %s.\n", argv[2]);
    return_status = STATUS_FILE_OPEN_ERROR;
    goto end;
  }

  if ((frame0 = calloc(frame_size, sizeof(unsigned char))) == NULL) {
    fprintf (stderr, "ERROR: unable to allocate memory.\n");
    return_status = STATUS_ALLOC_ERROR;
    goto end;
  }

  if ((frame1 = calloc(frame_size, sizeof(unsigned char))) == NULL) {
    fprintf (stderr, "ERROR: unable to allocate memory.\n");
    return_status = STATUS_ALLOC_ERROR;
    goto end;
  }

  max_frames = strtol(argv[5], NULL, 10);

  while ((number_of_frames < max_frames)
      && (fread(frame0, 1, frame_size, file0_ptr) == frame_size)
      && (fread(frame1, 1, frame_size, file1_ptr) == frame_size)) {
    unsigned char *ptr0 = frame0;
    unsigned char *ptr1 = frame1;

    for (i = 0; i < frame_size; ++i) {
      double diff = (*ptr1) - (*ptr0);
      total_sq_error += diff * diff;
      ++ptr0; ++ptr1;
    }
    ++number_of_frames;
  }

  if (number_of_frames > 0) {
    double samples = number_of_frames * frame_size;
    double total_psnr = mse2psnr(samples, 255.0, total_sq_error);
    fprintf(stdout, "%.3lf\n", total_psnr);
  }

end:
  if (frame0) free(frame0);
  if (frame1) free(frame1);
  if (file0_ptr) fclose(file0_ptr);
  if (file1_ptr) fclose(file1_ptr);

  return return_status;
}
