#if defined(UNITTEST) && defined(UNITTEST_LOG)
#define TLOG(FMT, ...) printf("    %d: " FMT "\n", __LINE__, __VA_ARGS__)
#else
#define TLOG(...)
#endif
