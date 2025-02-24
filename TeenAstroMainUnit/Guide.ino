// Guide ---------------------------------------------------------------------------------------------

// Guide, commands to move the mount in any direction at a series of fixed rates


void apply_GuidingA1()
{
  cli();
  staA1.target += guideA1.getAmount();
  sei();
}
void apply_GuidingA2()
{
  cli();
  staA2.target += guideA2.getAmount();
  sei();
}
void StopGuiding()
{
  guideA1.duration = -1;
  guideA2.duration = -1;
  cli();
  guideA1.brake();
  guideA2.brake();
  sei();
}
bool StopIfMountError()
{
  bool error = lastError != ERRT_NONE;
  if (error)
  {
    StopGuiding();
  }
  return error;
}

void PerformPulseGuiding()
{
  if (StopIfMountError())
    return;
  if (guideA2.duration <= 0 && guideA1.duration <= 0 )
  {
    cli();
    guideA1.brake();
    guideA2.brake();
    sei();
    return;
  }
  if (guideA1.isMoving())
  {
    if (guideA1.duration > 0)
    {
      if (!backlashA1.correcting)
      { 
        apply_GuidingA1();
        // for pulse guiding, count down the mS and stop when timed out
        guideA1.duration -= (long)(micros() - guideA1.durationLast);
        guideA1.durationLast = micros();        
      }
      else
      {
        guideA1.durationLast = micros();
      }
    }
    else
    {
      cli();
      guideA1.brake();
      sei();
    }
  }
  else
  {
    guideA1.duration = -1;
  }
  if (guideA2.isMoving())
  {
    if (guideA2.duration > 0 )
    {
      if (!backlashA2.correcting)
      {
        apply_GuidingA2();
        // for pulse guiding, count down the mS and stop when timed out
        guideA2.duration -= (long)(micros() - guideA2.durationLast);
        guideA2.durationLast = micros();
        
      }
      else
      {
        guideA2.durationLast = micros();
      }
    }
    else
    {
      cli();
      guideA2.brake();
      sei();
    } 
  }
  else
  {
    guideA2.duration = -1;
  }

}

void PerfomST4Guiding()
{
  if (StopIfMountError())
    return;
  if (guideA1.isMoving())
  {
    if (!backlashA1.correcting)
    {
      apply_GuidingA1();
    }
  }
  if (guideA2.isMoving())
  {
    if (!backlashA2.correcting)
    {
      apply_GuidingA2();
    }
  }
}

void PerfomGuidingRecenter()
{
  if (guideA1.isMoving())
  {
    if (!backlashA1.correcting)
    {
      apply_GuidingA1();
    }
  }
  if (guideA2.isMoving())
  {
    if (!backlashA2.correcting)
    {
      apply_GuidingA2();
    }
  }
}

void PerformGuidingAtRate()
{
  if (StopIfMountError())
    return;
  if (guideA1.isMoving())
  {
    if (!backlashA1.correcting)
    {
      cli();
      staA1.target += guideA1.getAmount();
      sei();
    }
  }
  if (guideA2.isMoving())
  {
    if (!backlashA2.correcting)
    {
      cli();
      staA2.target += guideA2.getAmount();
      sei();
    }
  }
}

void Guide()
{
  // 1/100 second sidereal timer, controls issue of steps at the selected RA and/or Dec rate(s)

  if (GuidingState == GuidingOFF)
  {
    return;
  }

  if (rtk.updateguideSiderealTimer())
  {
    if (GuidingState == GuidingPulse)
    {
      PerformPulseGuiding();
    }
    else if (GuidingState == GuidingST4)
    {
      PerfomST4Guiding();
    }
    else if (GuidingState == GuidingRecenter)
    {
      PerfomGuidingRecenter();
    }
    else if (GuidingState == GuidingAtRate)
    {
      PerformGuidingAtRate();
    }
  }
}

