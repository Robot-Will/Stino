
REMOVE := rm -rf
MV := mv -f
MKDIR := mkdir -p
SED := sed 
FIND := find 
DIRNAME := dirname 

########## Project Defination ##########
INO_SRC := $(shell $(FIND) -name "*.ino" | sed 's/\\ /\\\\ /g')
PDE_SRC := $(shell $(FIND) -name "*.pde" | sed 's/\\ /\\\\ /g')
C_SRC := $(shell $(FIND) -name "*.c" | sed 's/\\ /\\\\ /g')
CPP_SRC := $(shell $(FIND) -name "*.cpp" | sed 's/\\ /\\\\ /g')
A_SRC := $(shell $(FIND) -name "*.S" | sed 's/\\ /\\\\ /g')

PRJ_SRC := $(INO_SRC)
PRJ_SRC += $(PDE_SRC)

ifdef PRJ_SRC
ifneq "$(words $(PRJ_SRC))" "$(COUNT)"
$(error There is more than one .ino or .pde file in this directory!)
endif
endif

PRJ_BUILD_ROOT := build
PRJ_OBJ_ROOT := $(PRJ_BUILD_ROOT)/obj
TARGET := $(PRJ_BUILD_ROOT)/$(PRJ_NAME)

PRJ_OBJ := $(patsubst %.ino, $(PRJ_OBJ_ROOT)/%.ino.o, $(INO_SRC))
PRJ_OBJ += $(patsubst %.pde, $(PRJ_OBJ_ROOT)/%.ino.o, $(PDE_SRC))
PRJ_OBJ += $(patsubst %.c, $(PRJ_OBJ_ROOT)/%.c.o, $(C_SRC))
PRJ_OBJ += $(patsubst %.cpp, $(PRJ_OBJ_ROOT)/%.cpp.o, $(CPP_SRC))
PRJ_OBJ += $(patsubst %.S, $(PRJ_OBJ_ROOT)/%.s.o, $(A_SRC))

DEP_FILE := $(patsubst %.ino, $(PRJ_OBJ_ROOT)/%.dep, $(INO_SRC))
DEP_FILE += $(patsubst %.pde, $(PRJ_OBJ_ROOT)/%.dep, $(PDE_SRC))
DEP_FILE += $(patsubst %.c, $(PRJ_OBJ_ROOT)/%.dep, $(C_SRC))
DEP_FILE += $(patsubst %.cpp, $(PRJ_OBJ_ROOT)/%.dep, $(CPP_SRC))

########## Arduino Core Defination ##########

CORE_LIB := $(CORE_OBJ_ROOT)/$(CORE_LIB_NAME)

CORE_C_SRC := $(shell $(FIND) $(CORE_SOURCE_ROOT) -name "*.c" | sed 's/\\ /\\\\ /g')
CORE_CPP_SRC := $(shell $(FIND) $(CORE_SOURCE_ROOT) -name "*.cpp" | sed 's/\\ /\\\\ /g')

CORE_OBJ := $(patsubst $(CORE_SOURCE_ROOT)/%.c, $(CORE_OBJ_ROOT)/%.c.o, $(CORE_C_SRC))
CORE_OBJ += $(patsubst $(CORE_SOURCE_ROOT)/%.cpp, $(CORE_OBJ_ROOT)/%.cpp.o, $(CORE_CPP_SRC))

DEP_FILE += $(patsubst $(CORE_SOURCE_ROOT)/%.c, $(CORE_OBJ_ROOT)/%.dep, $(CORE_OBJ))
DEP_FILE += $(patsubst $(CORE_SOURCE_ROOT)/%.cpp, $(CORE_OBJ_ROOT)/%.dep, $(CORE_OBJ))

########## Flags Defination ##########
INO_FLAGS = $(CPP_FLAGS) -x c++ -include $(CORE_SOURCE_ROOT)/Arduino.h

########## Generating DEP Files ##########
# ifneq ($(MAKECMDGOALS), clean)
# sinclude $(DEP_FILE)
# endif

########## Default Rule ##########
.DEFAULT_GOAL := all

########## Rules ##########

.PHONY: all build echo_building clean clean_core clean_all upload size upload_by_programmer burn_bootloader

all: build

build: clean_all echo_building $(TARGET).$(HEX_EXT)
	@$(SIZE) $(SIZE_FLAGS) $(TARGET).$(SIZE_EXT)
#@echo Binary sketch size: $(HEXSIZE) bytes (of a $(MAX_SIZE) byte maximum)

echo_building:
	@echo Bulding $(TARGET).$(HEX_EXT)...

size: $(TARGET).elf
	echo && $(SIZE) --format=avr --mcu=$(MCU) $(TARGET).$(SIZE_EXT)

upload: build
	$(UPLOADER) $(UPLOAD_FLAGS)

upload_by_programmer: build
	$(UPLOADER) $(PROGRAM_FLAGS)

burn_bootloader:
	$(UPLOADER) $(ERASE_FLAGS)
	$(UPLOADER) $(BOOTLOADER_FLAGS)

clean_all: clean clean_core

clean:
	@echo cleaning Project Objects...
	@$(REMOVE) $(PRJ_BUILD_ROOT)

clean_core:
	@echo cleaning Arduino Core Objects...
	@$(REMOVE) $(CORE_OBJ_ROOT)


########## Building The Target Rules##########
$(TARGET).$(HEX_EXT): $(TARGET).elf
	$(BUILDING_VERBOSE)$(ELF2HEX) $(OBJCOPY_HEX_FLAGS) $< $@

$(TARGET).elf: $(PRJ_OBJ) $(CORE_LIB)
	$(BUILDING_VERBOSE)$(CELF) $(C_COMBINE_FLAGS1) -o $@ $(C_COMBINE_FLAGS2) $(PRJ_OBJ) $(C_COMBINE_FLAGS3) $(CORE_LIB) $(C_COMBINE_FLAGS4)

$(PRJ_OBJ_ROOT)/%.ino.o: %.ino
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)$(CPP) $(INO_FLAGS) $< -o $@

$(PRJ_OBJ_ROOT)/%.ino.o: %.pde
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)$(CPP) $(INO_FLAGS) $< -o $@

$(PRJ_OBJ_ROOT)/%.c.o: %.c
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)$(CC) $(C_FLAGS) $< -o $@

$(PRJ_OBJ_ROOT)/%.cpp.o: %.cpp
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)$(CPP) $(CPP_FLAGS) $< -o $@

$(PRJ_OBJ_ROOT)/%.s.o: %.S
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)$(CC) $(S_FLAGS) $< -o $@

########## The Target Dependence Rules##########
$(PRJ_OBJ_ROOT)/%.dep: %.ino
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)($(CPP) -MM $(INO_FLAGS) $< | $(SED) "s;$(notdir $*).o:;$(PRJ_OBJ_ROOT)/$*.o $(PRJ_OBJ_ROOT)/$*.dep:;") > $@

$(PRJ_OBJ_ROOT)/%.dep: %.pde
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)($(CPP) -MM $(INO_FLAGS) $< | $(SED) "s;$(notdir $*).o:;$(PRJ_OBJ_ROOT)/$*.o $(PRJ_OBJ_ROOT)/$*.dep:;") > $@

$(PRJ_OBJ_ROOT)/%.dep: %.c
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)($(CC) -MM $(C_FLAGS) $< | $(SED) "s;$(notdir $*).o:;$(PRJ_OBJ_ROOT)/$*.o $(PRJ_OBJ_ROOT)/$*.dep:;") > $@

$(PRJ_OBJ_ROOT)/%.dep: %.cpp
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)($(CPP) -MM $(CPP_FLAGS) $< | $(SED) "s;$(notdir $*).o:;$(PRJ_OBJ_ROOT)/$*.o $(PRJ_OBJ_ROOT)/$*.dep:;") > $@

########## Build  Arduino Core Libraries ##########
$(CORE_LIB): $(CORE_OBJ)
	$(BUILDING_VERBOSE)$(AR) $(AR_FLAGS) $@ $(CORE_OBJ)

$(CORE_OBJ_ROOT)/%.c.o: $(CORE_SOURCE_ROOT)/%.c
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)$(CC) $(C_FLAGS) $< -o $@

$(CORE_OBJ_ROOT)/%.cpp.o: $(CORE_SOURCE_ROOT)/%.cpp
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)$(CPP) $(CPP_FLAGS) $< -o $@

$(CORE_OBJ_ROOT)/%.dep: $(CORE_SOURCE_ROOT)/%.c
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)($(CC) -MM $(C_FLAGS) $< | $(SED) "s;$(notdir $*).o:;$(CORE_OBJ_ROOT)/$*.o $(CORE_OBJ_ROOT)/$*.dep:;") > $@

$(CORE_OBJ_ROOT)/%.dep: $(CORE_SOURCE_ROOT)/%.cpp
	@$(MKDIR) $(shell $(DIRNAME) $@)
	$(BUILDING_VERBOSE)($(CPP) -MM $(CPP_FLAGS) $< | $(SED) "s;$(notdir $*).o:;$(CORE_OBJ_ROOT)/$*.o $(CORE_OBJ_ROOT)/$*.dep:;") > $@