#if defined(UNITTEST)
#include "test.h"
#define TLOG(FMT, ...) _test_log("    * %s:%d: " FMT "\n", __FILE__, __LINE__, ##__VA_ARGS__)
#else
#define TLOG(...)
#endif
