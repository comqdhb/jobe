<?php defined('BASEPATH') OR exit('No direct script access allowed');

/* ==============================================================
 *
 * PHP5
 *
 * ==============================================================
 *
 * @copyright  2014 Richard Lobb, University of Canterbury
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

require_once('application/libraries/LanguageTask.php');

class Php_Task extends Task {
    public function __construct($source, $filename, $input, $params) {
        Task::__construct($source, $filename, $input, $params);
        $this->default_params['memorylimit'] = 20000000;
        if (isset($params['memorylimit']) && $params['memorylimit'] < 20000000) {
            $params['memorylimit'] = 20000000;  // Minimum for Java 8 JVM
        }
        //$this->default_params['interpreterargs'] = array('--no-php-ini');
        
    }

    public static function getVersionCommand() {
        return array('php --version', '/PHP ([0-9._]*)/');
    }

    public function compile() {
        $outputLines = array();
        $returnVar = 0;
        exec("/usr/bin/php -l {$this->sourceFileName} 2>compile.out",
                $outputLines, $returnVar);
        if ($returnVar == 0) {
            $this->cmpinfo = '';
            $this->executableFileName = $this->sourceFileName;
        }
        else {
            $output = implode("\n", $outputLines);
            $compileErrs = file_get_contents('compile.out');
            if ($output) {
                $this->cmpinfo = $output . '\n' . $compileErrs;
            } else {
                $this->cmpinfo = $compileErrs;
            }
        }
    }


    // A default name for PHP programs
    public function defaultFileName($sourcecode) {
        return 'prog.php';
    }


    public function getExecutablePath() {
        return '/usr/bin/php';
     }


     public function getTargetFile() {
         return $this->sourceFileName;
     }
};
