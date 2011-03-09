Interface flow:
          
          start CP

          query - existing or new project?
                existing -> browse -> obvious

          if new:
             image source:
                   96/384/1536/other plates?
                   unorganized?
                   CSV file with filenames/URLs
             image location
                   include subdirs (allow selection)
                   action: try to find metadata
                   ... if not available, ask how to extract
                   (and offer to extract, anyway? or should this be a
                        new module)
             excluding images (or strict inclusion).
             Put up platemap ASAP!
             
          At this point, we should have well/field/wavelength, and
             should offer to verify that every field has the same
             expected number and type of images.
             (but should start fetching in background, probably, anyway)

          Name channels for pipeline....

          And... action!

