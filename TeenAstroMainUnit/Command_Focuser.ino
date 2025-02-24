#include "Command.h"
//----------------------------------------------------------------------------------
//   F - Focuser
void Command_F()
{
  if (!hasFocuser )
  {
    if (command[1] == '?') strcpy(reply, "0#");
    else replyFailed();
    return;
  }
  bool focuserNoResponse = false;
  bool focuserShortResponse = false;
  char command_out[30] = ":";
  Focus_Serial.flush();
  while (Focus_Serial.available() > 0) Focus_Serial.read();
  strcat(command_out, command);
  strcat(command_out, "#");

  switch (command[1])
  {
  case '+':
  case '-':
  case 'g':
  case 'G':
  case 'P':
  case 'Q':
  case 's':
  case 'S':
  case '!':
  case '$':
    focuserNoResponse = true;
    break;
  case 'x':
  case '?':
  case '~':
  case 'M':
  case 'V':
    focuserNoResponse = false;
    focuserShortResponse = false;
    break;
  case 'O':
  case 'o':
  case 'I':
  case 'i':
  case 'W':
  case '0':
  case '1':
  case '2':
  case '3':
  case '4':
  case '5':
  case '6':
  case '7':
  case '8':
  case 'c':
  case 'C':
  case 'm':
  case 'r':
    focuserNoResponse = false;
    focuserShortResponse = true;
    break;
  default:
  {
    replyFailed();
    return;
    break;
  }
  }

  Focus_Serial.print(command_out);
  Focus_Serial.flush();

  if (!focuserNoResponse)
  {
    unsigned long start = millis();
    int pos = 0;
    char b = 0;
    while (millis() - start < 40)
    {
      if (Focus_Serial.available() > 0)
      {
        b = Focus_Serial.read();
        if (b == '#' && !focuserShortResponse)
        {
          reply[pos] = b;
          reply[pos+1] = 0;
          return;
        }
        reply[pos] = b;
        pos++;
        if (pos > 49)
        {
          replyFailed();
          return;
        }
        reply[pos] = 0;
        if (focuserShortResponse)
        {
          if (b != '1')
            replyFailed();
          return;
        }
      }

    }
    replyFailed();
  }
  else
  {
    replyNothing();
  }
}
